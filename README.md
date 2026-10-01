# Project ERASE Website

## A website where users can join events, read blog posts from the Project ERASE team, and learn more about how they can assist students in Guatemala.

### A user-friendly website that allows board members to consistently post new information about events and goals for Project ERASE.

### This website intends to serve as an online base of information regarding the operations, contributions, and needs of the Project ERASE team. It should include blog posts that board members can post covering relevant information or events about the project. The website should include an events calendar that provides guests a comprehensive list of activities run by Project ERASE, with the capability to RSVP to certain events. It should also include an interactive map, where board members can add locations that provide pop-up information about the impact the team has had on the locations they send supplies. It is also going to provide AI integration, in the form of a chatbot that can help users navigate to the information they wish to obtain.

## Installation

### Prerequisites

Python 3.12

### Add-ons

Django - Website framework to streamline building the application, with useful features that allow for secure handling of information.

### Installation Steps

1. Install Python for your machine (currently download Python 3.12): https://www.python.org/downloads/
2. Navigate to the mysite directory
3. Open a terminal and run python manage.py runserver

### Production database

The students, workshops, reports, and event calendar Django apps share one
database. Locally, the project uses `db.sqlite3`; in production, it uses the
Neon PostgreSQL connection string in `DATABASE_URL`. Set that variable in the
Vercel project's Production environment (and Preview if needed). The Neon CLI
link command pulls the URL into the ignored local `.env` file; it does not set
the Vercel environment variable for you. Because Vercel redacts sensitive
values when pulling them for a local CLI build, also add the same connection
string as a GitHub Actions repository secret named `DATABASE_URL`. The deploy
workflow uses it during the prebuild and logs only its URL scheme.

The production GitHub Actions job runs Django migrations against Neon before
deploying the website. The app-specific migrations create the student,
workshop, report, and event/RSVP tables in this shared database. Existing data
in a local SQLite file is not copied automatically.

The production workflow also ensures one Django superuser exists. Add these as
GitHub Actions repository secrets: `DJANGO_SUPERUSER_USERNAME`,
`DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD`. They are needed by
the workflow only; they do not need to be set in Vercel. The password is set
when the account is first created and is not reset on later deployments.

## Functionality

Currently this website is a skeleton site, meant to showcase the branding and design possibilities. There are text buttons at the top of the site, that allow you to navigate to different pages.

The floating [site guide](docs/site-guide.md) answers page-finding questions and summarizes the current page without an AI API or per-message compute cost.

## Known Problems

No known issues.

## Contributing

1. Fork the repository.
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request!

## Additional Documentation

TODO: Provide links to additional documentation that may exist in the repo, e.g.,
  * Sprint reports
  * User links

## License

https://github.com/McGavGav/Project-ERASE-Website/blob/main/LICENSE.txt

run the server by inputting: python manage.py runserver