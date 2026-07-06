# Test Plan

## Introduction

This document provides a basic test plan that verifies as much application
functionality as feasible.

The intention is to provide basic assurance that the application is functional,
and guard against regressions.

**This document is not intended to be an exhaustive test plan.**

## Test Plan Limitations

Scutes does not provide ability to completely delete batches (for example,
deleting a batch does *not* delete file attachments creates from the bacth).
This limits the testing that can be done in the Kubernetes test, qa, and prod
instances, because the changes made in the tests cannot be easily removed.

Because the test plan assumes a "clean slate" and imports a specific mbox file,
this test plan should only be used in:

* The local development environment
* The Kubernetes "sandbox"

## Test Plan Assumptions

This test plan assumes that the user can log in via CAS as an administrator
(i.e., is a member of the "Scutes-Administrator" group in Grouper).

## Test Plan Setup

This test plan assumes a "clean slate" setup.

### Sample mbox

The following steps use the "2022-10.mbox" from the
"WHCA Pool Reports Collection/1-Capture" directory
(<https://umd.app.box.com/folder/143930108192>) in Box.

Download the "2022-10.mbox" file to the "/tmp" directory on the local
workstation.

### Local Development Environment

For the local development environment, the simplest way to provide a clean
slate is to checkout and run the application in a new directory, following the
steps in [Development Environment](DevelopmentEnvironment.md) instructions.

The following steps assume that Scutes is already running locally.

local-Prep-1) In a terminal, switch to the "scutes" project directory.

local-Prep-2) Activate the Python environment:

```zsh
$ source .venv/bin/activate
```

local-Prep-3) Load the sample mbox file:

```zsh
$ src/manage.py load_mbox_data /tmp/2022-10.mbox
```

### Kubernetes "sandbox" namespace

For the Kubernetes "sandbox", any existing "scutes" stack should be deleted,
as well as the persistent volumes. The persistent volumes should then be
recreated for the version being tested, and the "scutes" stack for the test
version applied.

sandbox-Prep-1) Clone the "umd-lib/k8s-whpool" repository and switch into the
directory:

```zsh
$ git clone git@github.com:umd-lib/k8s-whpool.git
$ cd k8s-whpool
```

sandbox-Prep-2) Delete the "scutes" Kubernetes stack and persistent volumes:

```zsh
$ kubectl config use-context sandbox
$ kubectl delete -k scutes/overlays/sandbox
$ kubectl delete -k scutes/volumes/overlays/sandbox
```

sandbox-Prep-3) Change the stack the version being tested

```zsh
$ git checkout <NEW_VERSION>
```

sandbox-Prep-4) Create the persistent volumes and the "scutes" Kubernetes stack:

```zsh
$ kubectl apply -k scutes/volumes/overlays/sandbox
$ kubectl apply -k scutes/overlays/sandbox
```

sandbox-Prep-5) Upload the sample mbox to the "/var/opt/scutes/import" directory
in the "scutes-app-0" pod:

```zsh
$ kubectl cp /tmp/2022-10.mbox scutes-app-0:/var/opt/scutes/import
```

sandbox-Prep-6) Load the mbox file into scutes:

```zsh
$ kubectl exec -it scutes-app-0 -- /bin/bash
scutes-app-0$ src/manage.py load_mbox_data /var/opt/scutes/import/2022-10.mbox

# Delete the "2022-10.mbox" and exit
scutes-app-0$ rm /var/opt/scutes/import/2022-10.mbox
scutes-app-0$ exit
```

## Scute Test Plan

The test plan steps are specified using URLs for the Kubernetes "sandbox"
namespace. Unless otherwise specified, test steps should also work in the local
development environment.

### 1) Scutes Home Page

1.1) In a web browser, go to

* Kubernetes "sandbox": <https://scutes.sandbox.lib.umd.edu/>
* Local workstation: <http://scutes-local:15000/>

The Scutes home page will be displayed.

1.2) On the Scutes home page, verify that:

* The UMD favicon is displayed in the browser tab
* The appropriate SSDR environment banner is displayed
* The page contains a "Login with UMD account" button

1.3) At the bottom of the page, verify that the footer:

* Displays the application version number
* A "Log In" link
* Has a "Web Accessibility" link

1.3.1) Left-click the "Web Accessibility" link. Verify that the web
accessibility page on the university website is displayed.

1.3.2) Go back to the Scutes home page.

1.4) Left-click the "Login with UMD account" button. After logging in via CAS,
verify that the Scutes home page is displayed, and that the navigation bar
now contains a "Logged in as \<USERNAME>"  label, where \<USERNAME> is your
CAS username.

### 2) Dashboard Page

2.1) Left-click the "Dashboard" link in the navigation bar. The "Dashboard"
page will be displayed.

2.2) On the "Dashboard" page, verify that the page has the following sections
and content:

* Batches Assigned to \<USERNAME>

    The table in this section should be empty.

* Review Status

  * Displays a bar chart (Batch Name vs. Number of Items), with only one bar,
    for the "2022-10" batch, with 512 items

  * Underneath the chart are two panels:
    * All Items Review Status - all items should be in the "Not Started" status
    * Batch Review Completeness - "Number of Batches with No Items Started"
      should be 1

* Reporter and Item Statistics

  This section displays two panels, both of which should be populated with
  values:

  * Item totals and Items Publish by Reporter
  * Total Number of Reporters, Items, and Items Marked Published

### 3) Batch List Page

3.1) Left-click the "Batch List" link in the navigation bar. The "Batch List"
page will be displayed.

3.2) On the "Batch List" page, verify that there is a "2022-10" entry in the
table. Left-click the "Details" button for the entry. The "Batch Details"
page will be displayed.

3.3) On the "Batch Details" page, left-click the "Rerun Clean" button, and
then left-click the "OK" button to confirm. Verify that the panel below the
button displays the output of the cleaning operation, which should proceed
without error.

3.4) On the "Batch Details" page, left-click the "Rerun Mark Redactions" button,
and then left-click the "OK" button to confirm. Verify that the panel below the
button displays the output of the cleaning operation, which should proceed
without error.

3.5) Return to the "Batch List" page by left-clicking the "Batch List" link
in the navigation bar.

3.6) On the "Batch List" page, left-click the "Open" button for the "2022-02"
entry in the table. The "Item List" page will be displayed.

### 4) Item List Page

4.1) On the "Item" list page verify that:

* There is a table listing individual emails.
* A left sidebar with two panels:
  * Filters
  * "2022-10 Statistics"

4.2) In the "Filters" panel in the left sidebar, type a reporter's name, such
as `Smith` into the "Reporter Name Contains" field, and then left-click the
"Filter" button. Verify in the table that only entries with a "Reporter"
containing the name "Smith" are shown.

4.3) Clear the filter by left-click the "Clear All Filters" button. Verify that
the table now lists all entries.

4.4) Left-click the "Open" button for the first entry in the table. The
"Item View" page will be shown.

### 5) Item View Page

5.1) On the "Item View" page verify that:

* There is a subnavigation bar (to the right of the page title) with the
following buttons:

  * Prev Item
  * Next Item
  * List View with Fresh Start
  * List View with Current Filters

* The following fields are displayed and populated:
  * Date
  * Reporter
  * Title

* There is a two multiline panels side by side:
  * Body original
  * Body redact

  Both panels be populated with text, and below the panels should be
  word and character counts.

* A right sidebar with:
  * "Save & Next", "Save", and "Reset" buttons
  * A panel with the following checkbox/radio buttons:
    * Publish
    * Pool Report
    * Off the record
    * Editorial Review
      * Not started
      * In Progress
      * Complete
  * A "Notes" panel, which should be empty.

5.2) In the "Body redact" panel, scroll to the email signatures at the bottom of
the message and verify that the phone numbers and email address in the email
are redacted (displayed with a red line drawn through them).

5.4) Make the following changes on the page:

* In the "Body redact" panel, select the first paragraph in the email, and
left-click the "Redact"  button. A red line should be drawn through the text.
* In the right sidebar:
  * Left-click the "Publish" button to select it
  * In "Editorial Review", left-click the "Complete" radio button.

Then left-click the "Save & Next" button. Verify that the page refreshes and
shows a different email.

5.5) On the second email, in the right sidebar:

* Leave the "Publish" button unchecked
* Left-click the "Off the record" checkbox to select it
* In "Editorial Review", left-click the "Complete" radio button.

Then left-click the "Save & Next" button. Verify that the page refreshes and
shows a different email.

5.6) Left-click the "List View with Fresh Start" button. The "Item List" page
will be displayed.

5.7) On the "Item List" page verify that:

* The two entries in the table have an "Editorial Review" status of "Complete"
* The third entry in the table has an "Editorial Review" status of
"In Progress"

### 6) Export functionality

6.1) Left-click the "Batch List" link in the navigation bar. The "Batch List"
page will be shown.

6.2) On the "Batch List" page, in the "2022-10" batch, left-click the
"Convert for Export" button. The "Batch Convert for Export" page will be
displayed, with a modal popup dialog warning that not all items have been
reviewed. Left-click the "Proceed Anyway" button to ignore the warning and
continue.

6.3) On the "Batch Convert for Export" page, left-click the "Convert for Export"
button. The main panel on the page will be populated, and list only one email
as being exported (there will also be a warning about not all items in the batch
having been reviewed -- this is expected).

6.4) Left-click the "Batch List" link in the navigation bar. On the "Batch List"
page, verify that there the "2022-10" batch entry now has a "Download Batch"
button. Left-click the "Download Batch" button, and save the Zip file onto the
local workstation.

6.5) On the local workstation, unzip the file downloaded in the previous step.
Verify that the extracted contents include:

* A "whpool.csv" file
* A numbered folder, with an HTML file.

Display the HTML file in a web browser, and verify that:

* The first line is redacted (shows as a series of black squares).
* The phone number and email address in the email signature at the bottom of
the email are redacted.

### 7) Admin Page

7.1) In the Scutes application, left-click the "Admin" link in the navigation
bar. Verify that the "Scutes Admin" page will be displayed. This page is the
standard Django admin page.

7.2) Left-click the "View Site" link in the navigation bar to return to the
Scutes home page.

### 8) Logout

8.1) Left-click the "Logout" link in the navigation bar. Verify that A CAS page
is displayed indicating that the logout was successful.
