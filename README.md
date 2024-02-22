# Acs-Announcement-Notifier

Acs (Applied Computer Science) announcement notifier is a python app that scrapes announcements from three acs 
(http://www.acs.uns.ac.rs/sr) courses: Sistemi baza podataka (SBP), 
Inzenjering informacionih sistema (IIS) and Napredne arhitekture informacionih sistema (NAIS).
When it sees a new announcement it sends an email with content of the new announcement, so the subscribed user can stay up to date.

The app is integrated with AWS Lambda function, DynamoDB and AWS CloudWatch, so it could run every 10 minutes and notify
when the new updates occur. 