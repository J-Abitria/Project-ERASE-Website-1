# Sprint 4 Report (8/24/2026-9/30/2026)
## YouTube link of Sprint 4 Video ([YouTube Link](https://youtu.be/IP5ehLWUSDM))
## What's New (User Facing)
* Blogs can now be viewed by all visitors of the website.
* Administrator accounts have an engine to create blog posts with text and photos to be published on the website.
* Administrators can now review metrics from Project ERASE's Instagram posts to get insights on interactions with their social media page.
* A web assistant chatbot directs users that are unfamiliar with the layout to the pages they need.
## Work Summary (Developer Facing)
Each team member took on a specific feature that was discussed at the end of the previous semester to build on the feature set for the website. We had our initial set of features that included the payment gateway, blog system, social media integration, and web chatbot, but we chose to hold off on the implementation until we could meet with the client. This proved effective as we were able to change gears from setting up the payment gateway until the client had approval for utilizing a payment system, allowing us to focus on the deployment and the testability of the website. This sprint proved especially helpful in learning how to utilize external services with the application, utilizing GitHub Actions to automate testing, and setting up the production environment with a superuser an da production-size database.
## Unfinished Work
For this specific sprint, as described above, the payment gateway is on hold until the client can confirm that they are allowed to accept payments outside the organization. The rest of the work involves importing client data, which is currently just on hold while we wait to hear back from the client with more information, and making the UI styling configurable from an admin page rather than manually editing the code itself. Beyond this, the rest of the unfinished work involves making changes based on the client's feedback during validation testing.
## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:
* [Site Guide Assistant](https://github.com/J-Abitria/Project-ERASE-Website-1/pull/41)
* [Reports & Translation](https://github.com/J-Abitria/Project-ERASE-Website-1/pull/42)
* [Database and Blogging](https://github.com/J-Abitria/Project-ERASE-Website-1/pull/39)
## Code Files for Review
Please review the following code files, which were actively developed during this
sprint, for quality:
* [Blog Posting System Directory](https://github.com/J-Abitria/Project-ERASE-Website-1/tree/main/code/ERASEwebsite/blog)
* [instagram.py](https://github.com/J-Abitria/Project-ERASE-Website-1/blob/main/code/ERASEwebsite/reports/integrations/instagram.py)
* [sync_social_media.py](https://github.com/J-Abitria/Project-ERASE-Website-1/blob/main/code/ERASEwebsite/reports/management/commands/sync_social_media.py)
* [Reports views.py](https://github.com/J-Abitria/Project-ERASE-Website-1/blob/main/code/ERASEwebsite/reports/views.py)
* [site_guide.js](https://github.com/J-Abitria/Project-ERASE-Website-1/blob/main/code/ERASEwebsite/pages/static/pages/javascript/site_guide.js)
## Retrospective Summary
Here's what went well:
* Features were completed in time and adds more depth to the application
* Project is officially in a production environment
* Client is agreeable with the suggested features that were implemented with the sprint
* Adaptable to changes in plans for feature implementations with enough tasks to make significant progress
Here's what we'd like to improve:
* Being better prepared for client meetings and more proactive about scheduling
* Test coverage that highlights statement and branch coverage
* Centralized and configurable UI style for the website
Here are changes we plan to implement in the next sprint:
* Payment Gateway
* Editable color scheme and website logo image
* Integrating client data and making the website more presentable