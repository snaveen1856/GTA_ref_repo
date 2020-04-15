*** Settings ***
Library           lib.Setup    WITH NAME    setup
Library           lib.Teardown    WITH NAME    teardown

*** Variables ***
&{softreq}        linux=vdbench

*** Test Cases ***
test1
    [Tags]    TM-4135    Build Acceptance Test
    [Setup]    setup.Run
    Log    passed
    #Fail    Raising custom exception for Testing
    [Teardown]    teardown.Run

test2
    [Tags]    TM-4136    Build Acceptance Test
    [Setup]    setup.Run
    sleep    2s
    [Teardown]    teardown.Run

