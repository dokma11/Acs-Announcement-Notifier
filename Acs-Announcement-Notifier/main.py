from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import bs4
import smtplib
import boto3

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('LastAnnouncement')


def scrape_course(course_as, course_url, subject_for):
    course_announcement_array = course_as.split('|')

    course_last_h2 = course_announcement_array[0]
    course_last_em = course_announcement_array[1]

    if len(course_announcement_array) > 2:
        course_last_p = course_announcement_array[2]
    else:
        course_last_p = ''

    response = requests.get(course_url)

    if response.status_code == 200:
        format_response(response, course_last_h2, course_last_em, course_last_p, subject_for)
    else:
        print('Error:', response.status_code)


def format_response(response, last_h2, last_em, last_p, subject_for):
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    content_div = soup.find('div', class_='view-content')

    if content_div:
        p_tag = content_div.find('p')
        h2_tag = content_div.find('h2')
        em_tag = content_div.find('em')

        if h2_tag:
            print(h2_tag.get_text(strip=True))
        else:
            print('No <h2> tag found within the <div>')

        if em_tag:
            print(em_tag.get_text(strip=True))
        else:
            print('No <em> tag found within the <div>')

        if p_tag:
            print(p_tag.get_text(strip=True))
        else:
            print('No <p> tag found within the <div>')

        if (h2_tag.get_text(strip=True) != last_h2 or em_tag.get_text(strip=True) != last_em or
                p_tag.get_text(strip=True) != last_p):

            li_tag = content_div.find('li', class_='upload_attachments first last')

            if li_tag:
                link = li_tag.find('a').get('href')
                detailed_response = requests.get(f"http://www.acs.uns.ac.rs{link}")

                if detailed_response.status_code == 200:
                    detailed_soup = bs4.BeautifulSoup(detailed_response.text, 'html.parser')
                    detailed_content_div = detailed_soup.find('div', class_='node clear-block')

                    if detailed_content_div:
                        p_tag = detailed_content_div.find('p')

                        if p_tag:
                            print(p_tag.get_text(strip=True))
                        else:
                            print('No <p> tag found within the <div>')

                        a_tag = detailed_content_div.find('a').get('href')

                        if a_tag:
                            print(a_tag)
                            encoded_url = a_tag.replace(' ', '%20')
                        else:
                            print('No <a> tag found within the <div>')
                            encoded_url = ''
                    else:
                        print('No <div> found')
                        encoded_url = ''
                else:
                    print('Error with detailed response: ', detailed_response.status_code)
                    encoded_url = ''

            else:
                print('No link found')
                encoded_url = ''

            email_subject = 'ACS-Announcement'
            email_body = (f'{h2_tag.get_text(strip=True)}<br>{em_tag.get_text(strip=True)}<br><br>'
                          f'{p_tag.get_text(strip=True)}<br><br>{encoded_url}')

            send_email(email_subject, email_body.encode('utf-8'), 'vule.dok@gmail.com')
            send_email(email_subject, email_body.encode('utf-8'), 'kuzminacn@gmail.com')
            print('Emails sent')

            current_state = f"{last_h2}|{last_em}|{last_p}"
            # Have to get less detailed tags so that the comparisons would work properly
            p_tag = content_div.find('p')
            h2_tag = content_div.find('h2')
            em_tag = content_div.find('em')
            next_state = f"{h2_tag.get_text(strip=True)}|{em_tag.get_text(strip=True)}|{p_tag.get_text(strip=True)}"

            if subject_for == 'sbp':
                table.delete_item(
                    Key={
                        'announcement_state': current_state,
                        'announcement_id': 0
                    }
                )

                table.put_item(
                    Item={
                        'announcement_state': next_state,
                        'announcement_id': 0
                    }
                )

            if subject_for == 'iis':
                table.delete_item(
                    Key={
                        'announcement_state': current_state,
                        'announcement_id': 1
                    }
                )

                table.put_item(
                    Item={
                        'announcement_state': next_state,
                        'announcement_id': 1
                    }
                )

            if subject_for == 'nais':
                table.delete_item(
                    Key={
                        'announcement_state': current_state,
                        'announcement_id': 2
                    }
                )

                table.put_item(
                    Item={
                        'announcement_state': next_state,
                        'announcement_id': 2
                    }
                )

            print('Data updates went well')

        else:
            print('There are no new announcements')
    else:
        print('No <div> found')


def send_email(subject, body, recipient):
    msg = MIMEMultipart()

    msg['Subject'] = subject
    msg['From'] = 'acs.announcement@gmail.com'
    msg['To'] = recipient

    msg.attach(MIMEText(body.decode('utf-8'), 'html', 'utf-8'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('acs.announcement@gmail.com', 'bgpo jzev azpz brco')
        server.sendmail('acs.announcement@gmail.com', recipient, msg.as_string())


def lambda_handler(event, context):
    scan_response = table.scan()

    if 'Items' in scan_response:
        items = scan_response['Items']
        sbp_item = items[1]
        sbp_announcement_state = sbp_item.get('announcement_state', 'N/A')
        scrape_course(sbp_announcement_state, 'http://www.acs.uns.ac.rs/sr/sbp', 'sbp')

        iis_item = items[0]
        iis_announcement_state = iis_item.get('announcement_state', 'N/A')
        scrape_course(iis_announcement_state, 'http://www.acs.uns.ac.rs/sr/ism', 'iis')

        print('\n')

        nais_item = items[2]
        nais_announcement_state = nais_item.get('announcement_state', 'N/A')
        scrape_course(nais_announcement_state, 'http://www.acs.uns.ac.rs/sr/nais', 'nais')

    else:
        print("No items found")
