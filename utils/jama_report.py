"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for reading and filtering Jama item trace data reports.
"""
import json
import logging
import re

import voluptuous as vol
import yaml
from dateutil import parser as date_parser

import execute
from constants import JAMA_PARSER_BIN
from dictutils import dict_get_first
from strings import plainstr


# schema for verifying the Jama data structure
DATA_SCHEMA = vol.Schema([{
    vol.Required('downstream'): [{
        vol.Required('global_id'): plainstr,
        vol.Required('project_id'): plainstr,
        vol.Required('type'): plainstr,
        vol.Required('project'): plainstr,
        vol.Required('name'): plainstr
    }],
    vol.Required('fields'): vol.All(
        dict,
        lambda v: {plainstr(k): plainstr(x) for k, x in v.iteritems()}),
    vol.Required('location'): [plainstr],
    vol.Required('object_created'): vol.All(plainstr, date_parser.parse),
    vol.Required('object_modified'): vol.All(plainstr, date_parser.parse),
    vol.Required('object_type'): plainstr,
    vol.Required('project_id'): plainstr,
    vol.Required('report_path'): plainstr,
    vol.Required('tags'): [plainstr],
    vol.Required('title'): plainstr,
    vol.Required('upstream'): [{
        vol.Required('global_id'): plainstr,
        vol.Required('project_id'): plainstr,
        vol.Required('type'): plainstr,
        vol.Required('project'): plainstr,
        vol.Required('name'): plainstr
    }]
}])

# matches unescaped path separators in Jama location strings
LOCATION_RE = re.compile(r'(?<!\\)/')


def _location(v):
    """Location string validator"""
    return [
        x.replace('\\/', '/').replace('\\\\', '\\')
        for x in LOCATION_RE.split(v)]


def _recursive_conditions(v):
    """Recursive condition validator"""
    return vol.Any(
        vol.All(CONDITION_GROUP_SCHEMA, vol.Coerce(ConditionGroup)),
        vol.All(CONDITION_SCHEMA, vol.Coerce(Condition)))(v)


# schema constants
STR_CONTAINS = 'contains'
STR_DOES_NOT_CONTAIN = 'does not contain'
STR_IS = 'is'
STR_IS_NOT = 'is not'
STR_IN = 'in'
STR_NOT_IN = 'not in'
STR_MATCHES = 'matches'
DATE_BEFORE = 'before'
DATE_AFTER = 'after'
NUM_IS = 'is'
NUM_IS_NOT = 'is not'
NUM_IN = 'in'
NUM_NOT_IN = 'not in'
NUM_GREATER_THAN = 'greater than'
NUM_GREATER_THAN_EQ = 'greater than or equal to'
NUM_LESS_THAN = 'less than'
NUM_LESS_THAN_EQ = 'less than or equal to'
RELS_WITH_TYPE = 'with relationship type'
RELS_COUNT = 'count'
RELS_ALL_MATCH = 'all match'
RELS_COUNT_MATCH = 'count match'
RELS_NONE_MATCH = 'none match'
RELS_COUNT_UNKNOWNS = 'count unknowns'
LOCATION = 'location'
LOCATION_IS_UNDER = 'is under'
LOCATION_IS_NOT_UNDER = 'is not under'
LOCATION_EVERY_NODE = 'every node'
LOCATION_NO_NODE = 'no node'
FIELD = 'field'
FIELD_NAME = 'name'
FIELD_VALUE = 'value'
FIELD_REQUIRED = 'required'
CREATED = 'created'
MODIFIED = 'modified'
TAGS = 'tags'
TAGS_INCLUDE = 'include'
TAGS_EXCLUDE = 'exclude'
UPSTREAM_ITEMS = 'upstream items'
DOWNSTREAM_ITEMS = 'downstream items'
GROUP_TYPE = 'type'
GROUP_ALL = 'according to all'
GROUP_ANY = 'according to any'

# schema for filtering strings
STRCOMP_SCHEMA = vol.Schema({
    vol.Exclusive(STR_CONTAINS, 'str_compare'): plainstr,
    vol.Exclusive(STR_DOES_NOT_CONTAIN, 'str_compare'): plainstr,
    vol.Exclusive(STR_IS, 'str_compare'): plainstr,
    vol.Exclusive(STR_IS_NOT, 'str_compare'): plainstr,
    vol.Exclusive(STR_IN, 'str_compare'): [plainstr],
    vol.Exclusive(STR_NOT_IN, 'str_compare'): [plainstr],
    vol.Exclusive(STR_MATCHES, 'str_compare'): vol.All(
        plainstr,
        lambda v: re.compile(v, re.IGNORECASE))
}, extra=vol.PREVENT_EXTRA)

# schema for filtering dates
DATE_SCHEMA = vol.Schema({
    vol.Optional(DATE_BEFORE): vol.All(plainstr, date_parser.parse),
    vol.Optional(DATE_AFTER): vol.All(plainstr, date_parser.parse)
}, extra=vol.PREVENT_EXTRA)

# schema for filtering numbers
NUMCOMP_SCHEMA = vol.Any(
    vol.Schema({
        vol.Exclusive(NUM_IS, 'num_compare'): vol.Coerce(int),
        vol.Exclusive(NUM_IS_NOT, 'num_compare'): vol.Coerce(int),
        vol.Exclusive(NUM_IN, 'num_compare'): [vol.Coerce(int)],
        vol.Exclusive(NUM_NOT_IN, 'num_compare'): [vol.Coerce(int)]
    }, extra=vol.PREVENT_EXTRA),
    vol.Schema({
        vol.Exclusive(NUM_GREATER_THAN, 'gt'): vol.Coerce(int),
        vol.Exclusive(NUM_GREATER_THAN_EQ, 'gt'): vol.Coerce(int),
        vol.Exclusive(NUM_LESS_THAN, 'lt'): vol.Coerce(int),
        vol.Exclusive(NUM_LESS_THAN_EQ, 'lt'): vol.Coerce(int)
    }, extra=vol.PREVENT_EXTRA))

# schema for filtering relationships
RELATIONSHIPS_SCHEMA = vol.Schema({
    vol.Optional(RELS_WITH_TYPE): vol.Any(
        [plainstr], lambda v: [plainstr(v)]),
    vol.Optional(RELS_COUNT): NUMCOMP_SCHEMA,
    vol.Exclusive(RELS_ALL_MATCH, 'relationship_logic'): plainstr,
    vol.Exclusive(RELS_COUNT_MATCH, 'relationship_logic'): plainstr,
    vol.Exclusive(RELS_NONE_MATCH, 'relationship_logic'): plainstr,
    vol.Optional(RELS_COUNT_UNKNOWNS, default=False): vol.Boolean
}, extra=vol.PREVENT_EXTRA)

# schema for filtering items
CONDITION_SCHEMA = vol.Schema({
    vol.Exclusive(LOCATION, 'attribute'): vol.Schema({
        vol.Exclusive(LOCATION_IS_UNDER, 'location_logic'): _location,
        vol.Exclusive(LOCATION_IS_NOT_UNDER, 'location_logic'): _location,
        vol.Exclusive(LOCATION_EVERY_NODE, 'location_logic'): STRCOMP_SCHEMA,
        vol.Exclusive(LOCATION_NO_NODE, 'location_logic'): STRCOMP_SCHEMA
    }, extra=vol.PREVENT_EXTRA),
    vol.Exclusive(FIELD, 'attribute'): vol.Schema({
        vol.Required(FIELD_NAME): plainstr,
        vol.Optional(FIELD_VALUE): STRCOMP_SCHEMA,
        vol.Optional(FIELD_REQUIRED, default=True): vol.Coerce(bool)
    }, extra=vol.PREVENT_EXTRA),
    vol.Exclusive(CREATED, 'attribute'): DATE_SCHEMA,
    vol.Exclusive(MODIFIED, 'attribute'): DATE_SCHEMA,
    vol.Exclusive(TAGS, 'attribute'): vol.Schema({
        vol.Exclusive(TAGS_INCLUDE, 'tag_logic'): plainstr,
        vol.Exclusive(TAGS_EXCLUDE, 'tag_logic'): plainstr
    }, extra=vol.PREVENT_EXTRA),
    vol.Exclusive(UPSTREAM_ITEMS, 'attribute'): RELATIONSHIPS_SCHEMA,
    vol.Exclusive(DOWNSTREAM_ITEMS, 'attribute'): RELATIONSHIPS_SCHEMA
}, extra=vol.PREVENT_EXTRA)

# schema for filtering items with multiple conditions
CONDITION_GROUP_SCHEMA = vol.Schema({
    vol.Optional(GROUP_TYPE): vol.Any([plainstr], lambda v: [plainstr(v)]),
    vol.Exclusive(GROUP_ALL, 'group_logic'): [
        vol.Any(_recursive_conditions, plainstr)],
    vol.Exclusive(GROUP_ANY, 'group_logic'): [
        vol.Any(_recursive_conditions, plainstr)]
}, extra=vol.PREVENT_EXTRA)

# schema for a top-level filter
FILTER_SCHEMA = vol.All(
    dict,
    vol.Contains('main'),
    lambda v: {plainstr(k): _recursive_conditions(x) for k, x in v.iteritems()})


class InvalidCondition(Exception):
    """Exception raised when a condition definition is invalid"""
    pass


class Condition(object):
    """Condition to filter Jama items"""
    def __init__(self, condition):
        """
        Constructor called in instantiation.  Creates a condition which can be
        used to determine whether a Jama item should be filtered.

        :param condition: condition logic
        :type  condition: dict
        """
        self.location_logic = None
        self.location_path = None
        self.field_name = None
        self.field_logic = None
        self.field_value = None
        self.field_required = None
        self.created_before = None
        self.created_after = None
        self.modified_before = None
        self.modified_after = None
        self.tags_include = None
        self.tags_exclude = None
        self.upstream_type = None
        self.upstream_count = None
        self.upstream_logic = None
        self.upstream_condition = None
        self.upstream_count_unknowns = None
        self.downstream_type = None
        self.downstream_count = None
        self.downstream_logic = None
        self.downstream_condition = None
        self.downstream_count_unknowns = None

        # location
        location_condition = condition.get(LOCATION)
        if location_condition is not None:
            self.location_logic, location_value = dict_get_first(
                location_condition, [
                    LOCATION_IS_UNDER, LOCATION_IS_NOT_UNDER,
                    LOCATION_EVERY_NODE, LOCATION_NO_NODE])

            if self.location_logic in [
                    LOCATION_IS_UNDER, LOCATION_IS_NOT_UNDER]:
                self.location_path = location_value
                if self.location_logic is None:
                    raise InvalidCondition('Invalid location path "{}"'.format(
                        self.location_path))

            else:
                self.location_node_logic, self.location_node_value = (
                    dict_get_first(location_value, [
                        STR_CONTAINS, STR_DOES_NOT_CONTAIN, STR_IS,
                        STR_IS_NOT, STR_IN, STR_NOT_IN, STR_MATCHES]))

                if any(x is None for x in [
                        self.location_node_logic, self.location_node_value]):
                    raise InvalidCondition(
                        'Missing attribute for "{}" condition'.format(
                            self.location_logic))

            if self.location_logic is None:
                raise InvalidCondition(
                    'Missing attribute for "{}" condition'.format(LOCATION))

        # field
        field_condition = condition.get(FIELD)
        if field_condition is not None:
            self.field_name = field_condition.get(FIELD_NAME)
            field_value = field_condition.get(FIELD_VALUE)
            if field_value is not None:
                self.field_logic, self.field_value = dict_get_first(
                    field_value, [
                        STR_CONTAINS, STR_DOES_NOT_CONTAIN, STR_IS, STR_IS_NOT,
                        STR_IN, STR_NOT_IN, STR_MATCHES])

            self.field_required = field_condition.get(FIELD_REQUIRED, True)
            if self.field_name is None:
                raise InvalidCondition(
                    'Missing "{attr}" attribute for "{cnd}" condition'.format(
                        attr=FIELD_NAME, cnd=FIELD))

            if not self.field_required and all(x is None for x in [
                    self.field_value, self.field_value]):
                raise InvalidCondition(
                    'Missing "{attr}" attribute for "{cnd}" condition'.format(
                        attr=FIELD_VALUE, cnd=FIELD))

        # created
        created_condition = condition.get(CREATED)
        if created_condition is not None:
            self.created_before = created_condition.get(DATE_BEFORE)
            self.created_after = created_condition.get(DATE_AFTER)
            if all(x is None for x in [
                    self.created_before, self.created_after]):
                raise InvalidCondition(
                    'Missing attribute for "{}" condition'.format(CREATED))

        # modified
        modified_condition = condition.get(MODIFIED)
        if modified_condition is not None:
            self.modified_before = modified_condition.get(DATE_BEFORE)
            self.modified_after = modified_condition.get(DATE_AFTER)
            if all(x is None for x in [
                    self.modified_before, self.modified_after]):
                raise InvalidCondition(
                    'Missing attribute for "{}" condition'.format(MODIFIED))

        # tags
        tags_condition = condition.get(TAGS)
        if tags_condition is not None:
            self.tags_include = tags_condition.get(TAGS_INCLUDE)
            self.tags_exclude = tags_condition.get(TAGS_EXCLUDE)
            if all(x is None for x in [
                    self.tags_include, self.tags_exclude]):
                raise InvalidCondition(
                    'Missing attribute for "{}" condition'.format(TAGS))

        # upstream items
        upstream_condition = condition.get(UPSTREAM_ITEMS)
        if upstream_condition is not None:
            self.upstream_type = upstream_condition.get(RELS_WITH_TYPE)
            count = upstream_condition.get(RELS_COUNT)
            if count is not None:
                logic, comp_value = dict_get_first(
                    count, [NUM_IS, NUM_IS_NOT, NUM_IN, NUM_NOT_IN])

                if logic is not None:
                    self.upstream_count = [(logic, count[logic])]

                else:
                    self.upstream_count = []
                    for logic in [
                            NUM_GREATER_THAN, NUM_GREATER_THAN_EQ,
                            NUM_LESS_THAN, NUM_LESS_THAN_EQ]:
                        if logic in count:
                            self.upstream_count.append((logic, count[logic]))

                    if len(self.upstream_count) == 0:
                        raise InvalidCondition(
                            'Missing sub-attribute of attribute "{attr}" for '
                            '"{cnd}" condition'.format(
                                attr=RELS_COUNT, cnd=UPSTREAM_ITEMS))

            self.upstream_logic, self.upstream_condition = dict_get_first(
                upstream_condition,
                [RELS_ALL_MATCH, RELS_COUNT_MATCH, RELS_NONE_MATCH])

            self.upstream_count_unknowns = upstream_condition.get(
                RELS_COUNT_UNKNOWNS, False)

            if all(x is None for x in [
                    self.upstream_count, self.upstream_condition]):
                raise InvalidCondition(
                    'Missing attribute for "{}" condition'.format(
                        UPSTREAM_ITEMS))

            if self.upstream_count is None:
                if self.upstream_logic == RELS_COUNT_MATCH:
                    raise InvalidCondition(
                        'Attribute "{attr1}" must be used with attribute '
                        '"{attr2}"'.format(
                            attr1=RELS_COUNT, attr2=RELS_COUNT_MATCH))

            elif self.upstream_logic not in [None, RELS_COUNT_MATCH]:
                raise InvalidCondition(
                    'Attribute "{attr1}" cannot be combined with attribute '
                    '"{attr2}"'.format(
                        attr1=RELS_COUNT, attr2=self.upstream_logic))

        # downstream items
        downstream_condition = condition.get(DOWNSTREAM_ITEMS)
        if downstream_condition is not None:
            self.downstream_type = downstream_condition.get(RELS_WITH_TYPE)
            count = downstream_condition.get(RELS_COUNT)
            if count is not None:
                logic, comp_value = dict_get_first(
                    count, [NUM_IS, NUM_IS_NOT, NUM_IN, NUM_NOT_IN])

                if logic is not None:
                    self.downstream_count = [(logic, count[logic])]

                else:
                    self.downstream_count = []
                    for logic in [
                            NUM_GREATER_THAN, NUM_GREATER_THAN_EQ,
                            NUM_LESS_THAN, NUM_LESS_THAN_EQ]:
                        if logic in count:
                            self.downstream_count.append((logic, count[logic]))

                    if len(self.downstream_count) == 0:
                        raise InvalidCondition(
                            'Missing sub-attribute of attribute "{attr}" for '
                            '"{cnd}" condition'.format(
                                attr=RELS_COUNT, cnd=DOWNSTREAM_ITEMS))

            self.downstream_logic, self.downstream_condition = dict_get_first(
                downstream_condition,
                [RELS_ALL_MATCH, RELS_COUNT_MATCH, RELS_NONE_MATCH])

            self.downstream_count_unknowns = downstream_condition.get(
                RELS_COUNT_UNKNOWNS, False)

            if all(x is None for x in [
                    self.downstream_count, self.downstream_condition]):
                raise InvalidCondition(
                    'Missing attribute for "{}" condition'.format(
                        DOWNSTREAM_ITEMS))

            if self.downstream_count is None:
                if self.downstream_logic == RELS_COUNT_MATCH:
                    raise InvalidCondition(
                        'Attribute "{attr1}" must be used with attribute '
                        '"{attr2}"'.format(
                            attr1=RELS_COUNT, attr2=RELS_COUNT_MATCH))

            elif self.downstream_logic not in [None, RELS_COUNT_MATCH]:
                raise InvalidCondition(
                    'Attribute "{attr1}" cannot be combined with attribute '
                    '"{attr2}"'.format(
                        attr1=RELS_COUNT, attr2=self.downstream_logic))

    def __call__(self, item, item_map, named_conditions):
        """
        Determines whether or not a Jama item matches the condition logic.

        :param item: Jama item data
        :type  item: dict
        :param item_map: map of project IDs to Jama item data
        :type  item_map: dict{basestring:dict}
        :param named_conditions: map of condition names to conditions
        :type  named_conditions: dict{basestring:Condition}
        :return: whether the item matches the condition logic
        :rtype: bool
        """
        # location is under
        if self.location_logic == LOCATION_IS_UNDER:
            item_path = item['location'] + [item['title']]
            if len(item_path) < len(self.location_path):
                return False

            return all(
                item_path[i] == node
                for i, node in enumerate(self.location_path))

        # location is not under
        if self.location_logic == LOCATION_IS_NOT_UNDER:
            item_path = item['location'] + [item['title']]
            if len(item_path) < len(self.location_path):
                return True

            return not all(
                item_path[i] == node
                for i, node in enumerate(self.location_path))

        # location every node
        if self.location_logic == LOCATION_EVERY_NODE:
            item_path = item['location'] + [item['title']]
            return all(
                self._strcomp(value=node,
                    comp_value=self.location_node_value,
                    logic=self.location_node_logic)
                for node in item_path)

        # location no node
        if self.location_logic == LOCATION_NO_NODE:
            item_path = item['location'] + [item['title']]
            return all(
                not self._strcomp(value=node,
                    comp_value=self.location_node_value,
                    logic=self.location_node_logic)
                for node in item_path)

        # field
        if self.field_name is not None:
            value = item['fields'].get(self.field_name)
            if value is None:
                return not self.field_required

            if self.field_logic is None:
                return True

            return self._strcomp(
                value=value,
                comp_value=self.field_value,
                logic=self.field_logic)

        # created after
        if (self.created_after is not None and
                item['object_created'] <= self.created_after):
            return False

        # created before
        if (self.created_before is not None and
                item['object_created'] >= self.created_before):
            return False

        if any(x is not None for x in [
                self.created_after, self.created_before]):
            return True

        # modified after
        if (self.modified_after is not None and
                item['object_modified'] <= self.modified_after):
            return False

        # modified before
        if (self.modified_before is not None and
                item['object_modified'] >= self.modified_before):
            return False

        if any(x is not None for x in [
                self.modified_after, self.modified_before]):
            return True

        # tags include
        if self.tags_include is not None:
            return self.tags_include in item['tags']

        # tags exclude
        if self.tags_exclude is not None:
            return self.tags_exclude not in item['tags']

        # upstream items
        if any(x is not None for x in [
                self.upstream_logic, self.upstream_count]):
            condition = None
            if self.upstream_condition is not None:
                condition = named_conditions.get(self.upstream_condition)
                if condition is None:
                    raise InvalidCondition(
                        'Missing condition with name "{}"'.format(
                            self.upstream_condition))

            return self._evaluate_relationships(
                relationships=item['upstream'],
                types=self.upstream_type,
                logic=self.upstream_logic,
                count_unknowns=self.upstream_count_unknowns,
                count=self.upstream_count,
                condition=condition,
                item_map=item_map,
                named_conditions=named_conditions)

        # downstream items
        if any(x is not None for x in [
                self.downstream_logic, self.downstream_count]):
            condition = None
            if self.downstream_condition is not None:
                condition = named_conditions.get(self.downstream_condition)
                if condition is None:
                    raise InvalidCondition(
                        'Missing condition with name "{}"'.format(
                            self.downstream_condition))

            return self._evaluate_relationships(
                relationships=item['downstream'],
                types=self.downstream_type,
                logic=self.downstream_logic,
                count_unknowns=self.downstream_count_unknowns,
                count=self.downstream_count,
                condition=condition,
                item_map=item_map,
                named_conditions=named_conditions)

        raise InvalidCondition('No condition logic to evaluate')

    def _evaluate_relationships(
            self, relationships, types, logic, count_unknowns, count, condition,
            item_map, named_conditions):
        """
        Determines whether or not a Jama item's relationships match the
        relationship condition logic.

        :param relationships: Jama item relationships to evaluate
        :type  relationships: list[dict]
        :param types: relationship types to consider
        :type  types: list[basestring]
        :param logic: logic to determine how the relationships are evaluated
                      against the condition
        :type  logic: basestring
        :param count_unknowns:
        :type  count_unknowns: bool
        :param count: number comparison conditions used to evaluate the
                      relationship count against
        :type  count: dict{basestring: int}
        :param condition: nested condition to evaluate the relationships against
        :type  condition: Condition
        :param item_map: map of project IDs to Jama item data
        :type  item_map: dict{basestring:dict}
        :param named_conditions: map of condition names to conditions
        :type  named_conditions: dict{basestring:Condition}
        :return: whether the relationships match the condition logic
        :rtype: bool
        """
        # collect known items
        known_items = []
        num_unknowns = 0
        for relationship in relationships:
            if (types is not None and
                    relationship['type'] not in types):
                continue

            related_item = item_map.get(relationship['project_id'])
            if related_item is None:
                num_unknowns += 1
                continue

            known_items.append(related_item)

        if logic is None:
            # just count
            num_related_items = len(known_items)
            if count_unknowns:
                num_related_items += num_unknowns

            return all(
                self._numcomp(
                    value=num_related_items,
                    comp_value=value,
                    logic=logic)
                for logic, value in count)

        else:
            # invalid unknowns
            if (not count_unknowns and num_unknowns > 0 and
                    logic in [RELS_ALL_MATCH, RELS_NONE_MATCH]):
                return False

            # evaluate condition against related items
            if logic == RELS_COUNT_MATCH:
                num_items = (
                    sum(1 for u in known_items if condition(
                        u, item_map, named_conditions)) + num_unknowns)

                return all(
                    self._numcomp(
                        value=num_items,
                        comp_value=value,
                        logic=logic)
                    for logic, value in count)

            return self._relcomp(
                related_items=known_items,
                condition=condition,
                logic=logic,
                item_map=item_map,
                named_conditions=named_conditions)

    @staticmethod
    def _strcomp(value, comp_value, logic):
        """
        Evaluates a string against another value according to the given logic.

        :param value: string to evaluate
        :type  value: basestring
        :param comp_value: value to evaluate against
        :type  comp_value: basestring, list[basestring], or regex pattern
        :param logic: method used to compare the values
        :type  logic: basestring
        :return: whether the string matched the comparison value
        :rtype: bool
        """
        if logic == STR_CONTAINS:
            return comp_value in value

        if logic == STR_DOES_NOT_CONTAIN:
            return comp_value not in value

        if logic == STR_IS:
            return value == comp_value

        if logic == STR_IS_NOT:
            return value != comp_value

        if logic == STR_IN:
            return value in comp_value

        if logic == STR_NOT_IN:
            return value not in comp_value

        if logic == STR_MATCHES:
            return comp_value.match(value) is not None

        raise InvalidCondition(
            'Invalid string comparison logic "{}"'.format(logic))

    @staticmethod
    def _numcomp(value, comp_value, logic):
        """
        Evaluates a number against another value according to the given logic.

        :param value: number to evaluate
        :type  value: int or float
        :param comp_value: value to evaluate against
        :type  comp_value: int, float, or list[int or float]
        :param logic: method used to compare the values
        :type  logic: basestring
        :return: whether the number matched the comparison value
        :rtype: bool
        """
        if logic == NUM_IS:
            return value == comp_value

        if logic == NUM_IS_NOT:
            return value != comp_value

        if logic == NUM_IN:
            return value in comp_value

        if logic == NUM_NOT_IN:
            return value not in comp_value

        if logic == NUM_GREATER_THAN:
            return value > comp_value

        if logic == NUM_GREATER_THAN_EQ:
            return value >= comp_value

        if logic == NUM_LESS_THAN:
            return value < comp_value

        if logic == NUM_LESS_THAN_EQ:
            return value <= comp_value

        raise InvalidCondition(
            'Invalid number comparison logic "{}"'.format(logic))

    @staticmethod
    def _relcomp(related_items, condition, logic, item_map, named_conditions):
        """
        Evaluates related items against a condition according to the given
        logic.

        :param related_items: related items to evaluate
        :type  related_items: list[dict]
        :param condition: condition to evaluate against
        :type  condition: Condition
        :param logic: method used to combine the condition evaluations for the
                      whole item group
        :type  logic: basestring
        :param item_map: map of project IDs to Jama item data
        :type  item_map: dict{basestring:dict}
        :param named_conditions: map of condition names to conditions
        :type  named_conditions: dict{basestring:Condition}
        :return: whether the related items matched the condition
        :rtype: bool
        """
        if logic == RELS_ALL_MATCH:
            return all(
                condition(u, item_map, named_conditions)
                for u in related_items)

        if logic == RELS_NONE_MATCH:
            return all(
                not condition(u, item_map, named_conditions)
                for u in related_items)

        raise InvalidCondition(
            'Invalid relationship comparison logic "{}"'.format(logic))


class ConditionGroup(object):
    """Group of conditions to filter Jama items"""
    def __init__(self, condition):
        """
        Constructor called in instantiation.  Creates a condition group which
        can be used to determine whether a Jama item should be filtered
        according to multiple conditions.

        :param condition: condition group logic
        :type  condition: dict
        """
        self.type = condition.get(GROUP_TYPE)
        self.group_logic, self.conditions = dict_get_first(
            condition, [GROUP_ALL, GROUP_ANY])

        if self.type is None and len(self.conditions) == 0:
            raise InvalidCondition(
                'Condition group must specify a type and/or group of '
                'conditions')

    def __call__(self, item, item_map, named_conditions):
        """
        Determines whether or not a Jama item matches the condition group logic.

        :param item: Jama item data
        :type  item: dict
        :param item_map: map of project IDs to Jama item data
        :type  item_map: dict{basestring:dict}
        :param named_conditions: map of condition names to conditions
        :type  named_conditions: dict{basestring:Condition}
        :return: whether the item matches the condition group logic
        :rtype: bool
        """
        if self.type is not None:
            if item['object_type'] not in self.type:
                return False

        if self.conditions is None:
            return True

        conditions = []
        for condition in self.conditions:
            if isinstance(condition, basestring):
                named_condition = named_conditions.get(condition)
                if named_condition is None:
                    raise InvalidCondition(
                        'Missing condition with name "{}"'.format(condition))

                condition = named_condition

            conditions.append(condition)

        if self.group_logic == GROUP_ALL:
            return all(
                condition(item, item_map, named_conditions)
                for condition in conditions)

        if self.group_logic == GROUP_ANY:
            return any(
                condition(item, item_map, named_conditions)
                for condition in conditions)

        return True


class JamaFilter(object):
    """Filter used to filter sets of Jama items"""
    def __init__(self, conditions):
        """
        Constructor called in instantiation.  Creates a filter which can
        determine what items from a set of Jama items match nested condition
        logic.

        :param conditions: nested conditions logic
        :type  conditions: dict
        """
        self.main_condition = conditions.pop('main')
        self.named_conditions = conditions

    def __call__(self, items):
        """
        Filters items according to the conditions.

        :param items: Jama item data
        :type  items: list[dict]
        :return: all Jama items that matched the filter conditions
        :rtype: list[dict]
        """
        item_map = {item['project_id']: item for item in items}
        return [
            item for item in items
            if self.main_condition(item, item_map, self.named_conditions)]

    @classmethod
    def load(cls, file_handler):
        """
        Instantiates a filter based on condition logic from a YAML file.

        :param file_handler: handle to a YAML file which describes Jama filter
                             conditions
        :type  file_handler: file
        :return: a Jama filter based on the conditions in the file
        :rtype: JamaFilter
        """
        logging.debug('Reading filter...')
        conditions = yaml.safe_load(file_handler)

        logging.debug('Validating filter...')
        conditions = FILTER_SCHEMA(conditions)

        logging.debug('Parsing filter...')
        return cls(conditions)


def parse_jama_reports(reports_path):
    """
    Parses a trace data report generated from Jama (or a directory of trace data
    reports) and collects the item data as dictionaries.

    :param reports_path: path to the trace data report(s)
    :type  reports_path: basestring
    :return: parsed Jama item data
    :rtype: list[dict]
    """
    logging.info('Parsing Jama reports in "{}"...'.format(reports_path))
    jama_data, err = execute.communicate(
        command='{bin} -p {path}'.format(
            bin=JAMA_PARSER_BIN,
            path=reports_path),
        shell=True)

    logging.info('Validating data from Jama reports...')
    return DATA_SCHEMA(json.loads(jama_data))


def filter_jama_data(jama_data, jama_filter):
    """
    Filters Jama items based.

    :param jama_data: Jama item data or path to the trace data report(s)
    :type  jama_data: list[dict] or basestring
    :param jama_filter: Jama filter, nested condition map, or path to a filter
                        file
    :type  jama_filter: JamaFilter, dict{basestring:dict}, basestring
    :return: filtered Jama items
    :rtype: list[dict]
    """
    if isinstance(jama_data, basestring):
        jama_data = parse_jama_reports(jama_data)

    if isinstance(jama_filter, basestring):
        logging.info('Creating filter from "{}"...'.format(jama_filter))
        with open(jama_filter, 'r') as f:
            jama_filter = JamaFilter.load(f)

    elif isinstance(jama_filter, dict):
        jama_filter = JamaFilter(jama_filter)

    return jama_filter(jama_data)
