from email.mime.text import MIMEText
import requests
import bs4
import smtplib
import boto3

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table('LastAnnouncement')


def scrape_sbp(sbp_as):
    sbp_url = 'http://www.acs.uns.ac.rs/sr/sbp'

    sbp_announcement_array = sbp_as.split('|')
    sbp_last_h2 = sbp_announcement_array[0]
    sbp_last_em = sbp_announcement_array[1]

    if len(sbp_announcement_array) > 2:
        sbp_last_p = sbp_announcement_array[2]
    else:
        sbp_last_p = ''

    response = requests.get(sbp_url)

    if response.status_code == 200:
        format_response(response, sbp_last_h2, sbp_last_em, sbp_last_p, 'sbp')
    else:
        print('Error:', response.status_code)


def scrape_iis(iis_as):
    iis_url = 'http://www.acs.uns.ac.rs/sr/ism'

    iis_announcement_array = iis_as.split('|')
    iis_last_h2 = iis_announcement_array[0]
    iis_last_em = iis_announcement_array[1]

    if len(iis_announcement_array) > 2:
        iis_last_p = iis_announcement_array[2]
    else:
        iis_last_p = ''

    response = requests.get(iis_url)

    if response.status_code == 200:
        format_response(response, iis_last_h2, iis_last_em, iis_last_p, 'iis')
    else:
        print('Error:', response.status_code)


def scrape_nais(nais_as):
    nais_url = 'http://www.acs.uns.ac.rs/sr/nais'

    nais_announcement_array = nais_as.split('|')

    nais_last_h2 = nais_announcement_array[0]

    if len(nais_announcement_array) > 1:
        nais_last_em = nais_announcement_array[1]
        nais_last_p = nais_announcement_array[2]
    else:
        nais_last_em = ''
        nais_last_p = ''

    response = requests.get(nais_url)

    if response.status_code == 200:
        format_response(response, nais_last_h2, nais_last_em, nais_last_p, 'nais')
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
            email_subject = 'ACS-Announcement'
            email_body = f'{h2_tag.get_text(strip=True)}<br>{em_tag.get_text(strip=True)}<br><br>{p_tag.get_text(strip=True)}'
            send_email(email_subject, email_body.encode('utf-8'), 'vule.dok@gmail.com')
            send_email(email_subject, email_body.encode('utf-8'), 'kuzminacn@gmail.com')
            print('Emails sent')

            current_state = f"{last_h2}|{last_em}|{last_p}"
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
    msg = MIMEText(body, 'html', 'utf-8')

    msg['Subject'] = subject
    msg['From'] = 'acs.announcement@gmail.com'
    msg['To'] = recipient

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
        scrape_sbp(sbp_announcement_state)

        print('\n')

        iis_item = items[0]
        iis_announcement_state = iis_item.get('announcement_state', 'N/A')
        scrape_iis(iis_announcement_state)

        print('\n')

        nais_item = items[2]
        nais_announcement_state = nais_item.get('announcement_state', 'N/A')
        scrape_nais(nais_announcement_state)

    else:
        print("No items found")
