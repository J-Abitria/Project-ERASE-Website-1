# Sprint 5 Report (10/01/2026-10/31/2026)
## YouTube link of Sprint 5 Video
## What's New (User Facing)
* Client data of events, board member names, and news about Project ERASE was added to the site.
* Admins now have uploaded data about students supported, workshop attendance, and fundraising metrics.
* Improved layout of the website when on a mobile device.
## Work Summary (Developer Facing)
The team added more configurability to the website, by providing additional web pages for the client to change the website logo, and the website colors that are used in the UI elements, in the event that they wish to update their graphics in future years. The team also gathered the necessary information from the clients to update the information on the web pages to more accurately reflect the layout of the website after development is complete. The team also performed functional testing on the different features of the site, to ensure that whenever updates were made to production, all existing functionality was still as expected.
## Unfinished Work
The main unfinished work for this sprint was the website's AI-web scraping of the Instagram platform. This was mainly due to not receiving the Meta Graph API key from the client, which likely was just lost on the tasks to complete between communicating with the client related to all the data needed for the website. Some of the data wasn't already compiled for the client to hand over, so it took additional time for them to obtain the data for us.
## Completed Issues/User Stories
Here are links to the issues that we completed in this sprint:
* [Updated Home Pages](https://github.com/J-Abitria/Project-ERASE-Website-1/issues/52)
* [Improved Mobile App Layout](https://github.com/J-Abitria/Project-ERASE-Website-1/issues/51)
* [Migrating Client Data](https://github.com/J-Abitria/Project-ERASE-Website-1/issues/53)
## Incomplete Issues/User Stories
Here are links to issues we worked on but did not complete in this sprint:
* [Instagram Platform Linking](https://github.com/J-Abitria/Project-ERASE-Website-1/issues/55) <<Incomplete as API key isn't available yet from client.>>
## Code Files for Review
Please review the following code files, which were actively developed during this
sprint, for quality:
* [Cloudinary Uploads](https://github.com/J-Abitria/Project-ERASE-Website-1/blob/main/code/ERASEwebsite/pages/cloudinary_uploads.py)
* [Web Configuration Settings Page](https://github.com/J-Abitria/Project-ERASE-Website-1/blob/main/code/ERASEwebsite/pages/templates/website_theme.html)
* [Web Configuration Models](https://github.com/J-Abitria/Project-ERASE-Website-1/blob/main/code/ERASEwebsite/pages/models.py)
* [Web Map Directory](https://github.com/J-Abitria/Project-ERASE-Website-1/tree/main/code/ERASEwebsite)
## Retrospective Summary
Here's what went well:
* Importing the data worked great with the existing systems once organized
* The feature set was able to be finalized and just waiting for client feedback.
Here's what we'd like to improve:
* Improve some of the UI elements from the more simple designs.
* Reach out more consistently to the client to ensure that as much feedback on the site can be received as possible.
Here are changes we plan to implement in the next sprint:
* Any client feedback received for the deployed web application.