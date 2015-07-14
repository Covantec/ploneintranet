*** Settings ***

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot
Resource  ../lib/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote
Library  DebugLibrary

Test Setup  Prepare test browser
Test Teardown  Close all browsers

*** Test Cases ***

Alice can view her own profile
    Given I am logged in as the user alice_lindstrom
    Then I can open the personal tools menu
    And I can follow the link to my profile

Alice cannot view her personal preferences
    Given I am logged in as the user alice_lindstrom
    When I open the personal preferences page
    Then The page is not found

Alice cannot open the password reset form
    Given I am logged in as the user alice_lindstrom
    When I open the password reset form
    Then The page is not found

Allan can view Alice's profile
    Given I am logged in as the user allan_neece
    Then I can view the profile for user alice_lindstrom
    And I can see details for Alice Lindström

Allan can follow Christian
    Given I am logged in as the user allan_neece
    Then I can view the profile for user christian_stoney
    And I can follow Christian Stoney
    Then I can open the personal tools menu
    And I can follow the link to my profile
    And I can see Christian Stoney in the list of users being followed

Dollie can unfollow Guy
    Given I am logged in as the user dollie_nocera
    Then I can view the profile for user guy_hackey
    And I can unfollow Guy Hackey
    Then I can open the personal tools menu
    And I can follow the link to my profile
    And I cannot see Guy Hackey in the list of users being followed

Dollie can change her details
    Given I am logged in as the user dollie_nocera
    And I can view the profile for user dollie_nocera
    Then I can change my name to Mickey

Dollie cannot change Guy's details
    Given I am logged in as the user dollie_nocera
    And I can view the profile for user guy_hackey
    Then I cannot edit personal details

*** Keywords ***

I can open the personal tools menu
    Click Element  css=header #user-avatar
    Wait Until Element Is Visible  css=.tooltip-container #portal-personaltools a#user-name

I open the personal preferences page
    Go To  ${PLONE_URL}/@@personal-preferences

I can follow the link to my profile
    Click Element  css=.tooltip-container #portal-personaltools a#user-name

I can view the profile for user ${USERID}
    Go To  ${PLONE_URL}/profiles/${USERID}

I can see details for ${NAME}
    Page should contain  ${NAME}

I can follow ${NAME}
    Click Element  css=button[title="Click to follow ${NAME}"]
    Wait Until Page Contains  Unfollow

I can unfollow ${NAME}
    Click Element  css=button[title="Click to unfollow ${NAME}"]
    Wait Until Page Contains  Follow

I can see ${NAME} in the list of users being followed
    Click Element  css=nav.tabs a.link-following
    Page should contain Element  jquery=#person-following a strong:contains("${NAME}")

I cannot see ${NAME} in the list of users being followed
    Click Element  css=nav.tabs a.link-following
    Page should not contain Element  jquery=#person-following a strong:contains("${NAME}")

I can change my name to ${NAME}
    Click Element  link=Info
    Wait Until Page Contains Element  css=#user-edit-form
    Input Text  name=form.widgets.first_name  Mickey
    Click button  name=form.buttons.save
    Page should contain Element  jquery=h1:contains("Mickey")

I cannot edit personal details
    Click Element  link=Info
    Page Should Contain Element  css=dt.icon-user
