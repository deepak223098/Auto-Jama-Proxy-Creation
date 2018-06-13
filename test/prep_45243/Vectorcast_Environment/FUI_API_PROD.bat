del commands.tmp
echo options ADA_DEBUG_CMD gps.exe --debug= >> commands.tmp
echo options COMPILATION_SYSTEM GNAT >> commands.tmp
echo options C_COMPILER_CFG_SOURCE CONFIG_FILE_63 >> commands.tmp
echo options GNATCHOP_OPTIONS -gnat95 >> commands.tmp
echo options GPR_OPTIONS -XKind=vectorcast >> commands.tmp
echo options MAX_VARY_RANGE 1000 >> commands.tmp
echo options RANGE_CHECK FULL >> commands.tmp
echo options RANGE_FILE_MAX_SIZE 10000000 >> commands.tmp
echo options TARGET_VARIANT HOST >> commands.tmp
echo options UNCON_ARRAY_SIZE 1000 >> commands.tmp
echo options VCAST_ADA_LANGUAGE_SPECIFICATION ADA_95 >> commands.tmp
echo options VCAST_COMMAND_LINE_DEBUGGER TRUE >> commands.tmp
echo options VCAST_COMPILE_GENERIC_STUBS TRUE >> commands.tmp
echo options VCAST_DISPLAY_UNINST_EXPR TRUE >> commands.tmp
echo options VCAST_DONT_STUB_ANCESTORS FALSE >> commands.tmp
echo options VCAST_EMPTY_TESTCASE_FAIL TRUE >> commands.tmp
echo options VCAST_ENABLE_FUNCTION_CALL_COVERAGE FALSE >> commands.tmp
echo options VCAST_EXPECTED_BEFORE_UUT_CALL TRUE >> commands.tmp
echo options VCAST_FILE_VERSION_COMMAND $(VECTORCAST_ADA_DIR)\\IO\\configurable\\version.bat >> commands.tmp
echo options VCAST_GNAT_INCLUDE_PATH $(G_HOST_COMPILER_DIR)\\lib\\gcc\\i686-pc-mingw32\\4.9.3\\adainclude >> commands.tmp
echo options VCAST_GNAT_OBJECTS_PATH $(G_HOST_COMPILER_DIR)\\lib\\gcc\\i686-pc-mingw32\\4.9.3\\adalib >> commands.tmp
echo options VCAST_GPR_USES_NAMING TRUE >> commands.tmp
echo options VCAST_INSTRUMENT_ASSIGNMENTS TRUE >> commands.tmp
echo options VCAST_INSTRUMENT_PARAMETERS TRUE >> commands.tmp
echo options VCAST_MAX_STRING_LENGTH 2000 >> commands.tmp
echo options VCAST_NEW_ARCHITECTURE TRUE >> commands.tmp
echo options VCAST_NO_STANDARD_PKG_USAGE TRUE >> commands.tmp
echo options VCAST_PRAGMA_IMPORT TRUE >> commands.tmp
echo options VCAST_RPTS_DEFAULT_FONT_FACE Arial(8) >> commands.tmp
echo options VCAST_RPTS_SHOW_VERSION TRUE >> commands.tmp
echo options VCAST_UNCONSTRAINED_STRING_SIZE 100 >> commands.tmp
echo options VCAST_USE_COMPOUND_FOR_BATCH FALSE >> commands.tmp
echo options VCAST_USE_GNATMAKE TRUE >> commands.tmp
echo options VCAST_USE_GPRBUILD TRUE >> commands.tmp
echo options WHITEBOX YES >> commands.tmp
echo environment build FUI_API_PROD.env >> commands.tmp
echo /E:FUI_API_PROD tools script run FUI_API_PROD.tst >> commands.tmp
echo /E:FUI_API_PROD execute batch >> commands.tmp
echo /E:FUI_API_PROD reports custom management FUI_API_PROD_management_report.html >> commands.tmp
"%VECTORCAST_DIR%\CLICAST"  /X:HOST /L:ADA tools execute commands.tmp false
