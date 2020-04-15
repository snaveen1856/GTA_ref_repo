*** Settings ***
Library           lib.Setup    WITH NAME    setup
Library           lib.Teardown    WITH NAME    teardown
Variables         TestData/test.yaml

*** Variables ***


*** Test Cases ***
test1
    [Tags]    TM-4135    Build Acceptance Test
    [Setup]    setup.Run
    Log    passed
    Log    ${test.test2}
    [Teardown]    teardown.Run

test2
    [Tags]    TM-4136    Build Acceptance Test
    [Setup]    setup.Run
    sleep    2s
    [Teardown]    teardown.Run

