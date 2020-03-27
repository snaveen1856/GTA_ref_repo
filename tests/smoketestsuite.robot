*** Settings ***
Library           lib.Setup    WITH NAME    setup
Library           lib.Teardown    WITH NAME    teardown

*** Variables ***
&{softreq}        linux=vdbench

*** Test Cases ***
test1
    [Tags]    TM-4135    Build Acceptance Test
    [Setup]    setup.Run
    Log    $device.ip}
    Fail    Raising custom exception for Testing
    [Teardown]    teardown.Run

test2
    [Tags]    TM-4136    Build Acceptance Test
    [Setup]    setup.Run
    sleep    2s
    [Teardown]    teardown.Run

test3
    [Tags]    TM-4137    Build Acceptance Test
    [Setup]    setup.Run    depends=test1
    log    test3
    [Teardown]    teardown.Run

test4
    [Tags]    TM-4138    Build Acceptance Test
    [Setup]    setup.run    depends=test1,test2
    log    test4
    [Teardown]    teardown.run

test5
    [Tags]    TM-4139    Must Pass Test
    [Setup]    setup.run
    log    ${device.username}
    [Teardown]    teardown.run

test6
    [Tags]    TM-4140    Feature Acceptance Test
    [Setup]    setup.run
    log    ${device.password}
    [Teardown]    teardown.run
