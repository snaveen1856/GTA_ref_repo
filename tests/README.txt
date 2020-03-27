This folder shall contain all the automated test cases specific to SUTAS Automation framework

Contains smoke testsuite for SUTAS.

After installation of SUTAS run this testsuite to verify if basic functionality of SUTAS is working or not.

this folder contains 3 files
1. smoketestsuite.robot -->  Actual testsuite 
2. smoke_test_config.yaml  --> Config file used by smoketestsuite
3. runtests.txt  -->  argfile to be executed which contains smoketestsuite.robot to be executed for 2 Cycles and 2 Minutes.


perform below steps:

After installation of SUTAS, move to tests director.

1. run "sutas user_setup"
2. run "sutas execute runtests.txt" expected output is 
	Test1 --> Fail
	Test2 --> Pass
	Test3 --> Skip since dependent test failed
	Test4 --> Skip since dependent test failed
	Test5 --> Pass
	Test6 --> Pass
3. run single test using -t option, command is "sutas execute -c smoke_test_config.yaml -s smoketestsuite.robot -t test1"
4. Run testsuite for 2 cycles using -d option "sutas execute -c smoke_test_config.yaml -s smoketestsuite.robot -d 2C"
5. Run testsuite for 2 cycles using -d option "sutas execute -c smoke_test_config.yaml -s smoketestsuite.robot -d 2M"





