del commands.tmp
echo options ADACAST_IO_BODY C:\\rw_apps\\vectorcast\\6.4n\\IO\\configurable\\adacast_io.adb-basic >> commands.tmp
echo options ADA_DEBUG_CMD powerpc-xcoff-lynxos178-gdb >> commands.tmp
echo options ADA_EXECUTE_CMD C:\\rw_apps\\vectorcast\\6.4n\\IO\\configurable\\rockwell.bat >> commands.tmp
echo options COMPILATION_SYSTEM GNAT >> commands.tmp
echo options C_COMPILER_CFG_SOURCE CONFIG_FILE_63 >> commands.tmp
echo options EVENT_LIMIT 99999999 >> commands.tmp
echo options FLOATING_POINT_TOLERANCE  >> commands.tmp
echo options GNATCHOP_OPTIONS -gnat95 >> commands.tmp
echo options GPR_OPTIONS -XKind=target_dev >> commands.tmp
echo options MAX_VARY_RANGE 1000 >> commands.tmp
echo options PREPARE_COMPILED_IN_DATA c:\\rw_apps\\python\\Python27\\python C:\\rw_apps\\vectorcast\\6.4n\\IO\\configurable\\CompiledInData.py --compiler gnat >> commands.tmp
echo options RANGE_CHECK FULL >> commands.tmp
echo options RANGE_FILE_MAX_SIZE 10000000 >> commands.tmp
echo options TARGET_COMMAND_VERB powerpc-xcoff-lynxos178 >> commands.tmp
echo options TARGET_SUPPORTS_TIC_IMAGE FALSE >> commands.tmp
echo options TARGET_VARIANT MISC_GNAT >> commands.tmp
echo options VCAST_ADA_ACCESSOR_FUNCTIONS TRUE >> commands.tmp
echo options VCAST_ALLOW_STUB_OF_STD_LIB FALSE >> commands.tmp
echo options VCAST_COMMAND_LINE_DEBUGGER FALSE >> commands.tmp
echo options VCAST_COMPILE_DUMB_STUBS TRUE >> commands.tmp
echo options VCAST_COMPILE_GENERIC_STUBS TRUE >> commands.tmp
echo options VCAST_CONFIGURABLE_ADA_IO TRUE >> commands.tmp
echo options VCAST_DISPLAY_FUNCTION_COVERAGE TRUE >> commands.tmp
echo options VCAST_DISPLAY_UNINST_EXPR TRUE >> commands.tmp
echo options VCAST_EMPTY_TESTCASE_FAIL TRUE >> commands.tmp
echo options VCAST_ENABLE_FUNCTION_CALL_COVERAGE FALSE >> commands.tmp
echo options VCAST_EXPECTED_BEFORE_UUT_CALL TRUE >> commands.tmp
echo options VCAST_FILE_VERSION_COMMAND C:\\rw_apps\\vectorcast\\6.4n\\IO\\configurable\\version.bat >> commands.tmp
echo options VCAST_FLOAT_PRECISION 0 >> commands.tmp
echo options VCAST_GNAT_INCLUDE_PATH C:\\rw_apps\\gnat\\7.2.8_ppc_lynx178-windows\\lib\\gcc\\powerpc-xcoff-lynxos178\\4.7.4\\rts-pthread\\adainclude >> commands.tmp
echo options VCAST_GNAT_OBJECTS_PATH C:\\rw_apps\\gnat\\7.2.8_ppc_lynx178-windows\\lib\\gcc\\powerpc-xcoff-lynxos178\\4.7.4\\rts-pthread\\adalib >> commands.tmp
echo options VCAST_GPR_USES_NAMING TRUE >> commands.tmp
echo options VCAST_MAX_STRING_LENGTH 2000 >> commands.tmp
echo options VCAST_MAX_TARGET_FILES 2048 >> commands.tmp
echo options VCAST_NEW_ARCHITECTURE TRUE >> commands.tmp
echo options VCAST_NO_STANDARD_PKG_USAGE TRUE >> commands.tmp
echo options VCAST_PRAGMA_IMPORT TRUE >> commands.tmp
echo options VCAST_PRE_EXECUTE_CMD  >> commands.tmp
echo options VCAST_RECOMPILE_SEPARATES FALSE >> commands.tmp
echo options VCAST_RPTS_DEFAULT_FONT_FACE Arial(8) >> commands.tmp
echo options VCAST_RPTS_SHOW_VERSION TRUE >> commands.tmp
echo options VCAST_SORT_METRICS_RPT_BY_DIR TRUE >> commands.tmp
echo options VCAST_STRICT_TEST_CASE_IMPORT FALSE >> commands.tmp
echo options VCAST_UNCONSTRAINED_STRING_SIZE 128 >> commands.tmp
echo options VCAST_USER_CONSTRAINTS INTERFACES.UNSIGNED_32 >> commands.tmp
echo options VCAST_USE_COMPOUND_FOR_BATCH TRUE >> commands.tmp
echo options VCAST_USE_GNATMAKE FALSE >> commands.tmp
echo options VCAST_USE_GPRBUILD TRUE >> commands.tmp
echo options VCAST_WIDE_CHARACTER_SUPPORT TRUE >> commands.tmp
echo options WHITEBOX YES >> commands.tmp
echo environment build FUI_API_PROD.env >> commands.tmp
echo /E:FUI_API_PROD tools script run FUI_API_PROD.tst >> commands.tmp
echo /E:FUI_API_PROD execute batch >> commands.tmp
echo /E:FUI_API_PROD reports custom management FUI_API_PROD_management_report.html >> commands.tmp
"%VECTORCAST_DIR%\CLICAST"  /X:MISC_GNAT /L:ADA tools execute commands.tmp false
