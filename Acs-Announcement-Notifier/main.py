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
    content_div = soup.find('div', class_='views-row views-row-1 views-row-odd views-row-first')

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

            if content_div.find('li', class_='upload_attachments first last'):
                li_tag = content_div.find('li', class_='upload_attachments first last')
            elif content_div.find('li', class_='node_read_more first last'):
                li_tag = content_div.find('li', class_='node_read_more first last')
            else:
                # Just put a radnom value so the rest of the script could work
                li_tag = content_div.find('li', class_='upload_attachments first last')

            detailed_paragraphs = False

            if li_tag:
                link = li_tag.find('a').get('href')
                detailed_response = requests.get(f"http://www.acs.uns.ac.rs{link}")

                if detailed_response.status_code == 200:
                    detailed_soup = bs4.BeautifulSoup(detailed_response.text, 'html.parser')
                    detailed_content_div = detailed_soup.find('div', class_='node clear-block')

                    if detailed_content_div:

                        order_of_elements = []
                        new_content_div = detailed_content_div.find('div', class_='content')
                        for index, element in enumerate(new_content_div.children):
                            if element.name:
                                order_of_elements.append((index, element.name))

                        for index, tag_name in order_of_elements:
                            print(f"Element {index}: {tag_name}")

                        p_tags = detailed_content_div.find_all('p')
                        print('Detailed p_tags length: ', len(p_tags))
                        if p_tags:
                            if len(p_tags) > 1:
                                p_tag = ''
                                for p in p_tags:
                                    p_tag += p.get_text(strip=True) + '<br><br>'
                            else:
                                p_tag = p_tags[0].get_text(strip=True)

                            print('p tag detailed: ', p_tag)
                            detailed_paragraphs = True
                        else:
                            print('No <p> tag found within the <div>')

                        a_tag = detailed_content_div.find('a').get('href')

                        if a_tag:
                            print(a_tag)
                            encoded_url = a_tag.replace(' ', '%20')
                            print('Encoded url: ', encoded_url)
                        else:
                            print('No <a> tag found within the <div>')
                            encoded_url = ''

                        ul_tags = detailed_content_div.find_all('ul')

                        if ul_tags:
                            li_tag = ''
                            for ul in ul_tags:
                                li_tags = ul.find_all('li')
                                for li in li_tags:
                                    li_tag += '<hr>- ' + li.get_text(strip=True) + '<br>'
                        else:
                            print('No <ul> tag found within the <div>')

                        final_body = ''
                        p_i = 0
                        u_i = 0
                        for index, tag_name in order_of_elements:
                            if tag_name == 'p':
                                final_body += p_tags[p_i].get_text(strip=True) + '<br><br>'
                                p_i += 1
                            elif tag_name == 'ul':
                                li_tag = ''
                                li_tags = ul_tags[u_i].find_all('li')
                                for li in li_tags:
                                    li_tag += '&nbsp;- ' + li.get_text(strip=True) + '<br>'

                                final_body += li_tag
                                u_i += 1

                        print('Final body je: ' + final_body)

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

            if detailed_paragraphs:
                email_body = (f'{h2_tag.get_text(strip=True)}<br>{em_tag.get_text(strip=True)}<br><br>'
                              f'{final_body}{encoded_url}')
            else:
                email_body = (f'{h2_tag.get_text(strip=True)}<br>{em_tag.get_text(strip=True)}<br><br>'
                              f'{p_tag.get_text(strip=True)}{li_tag}<br>{encoded_url}')

            print('Email body: ', email_body)

            send_email(email_subject, email_body.encode('utf-8'), 'vule.dok@gmail.com')
            send_email(email_subject, email_body.encode('utf-8'), 'kuzminacn@gmail.com')
            print('Emails sent')

            current_state = f"{last_h2}|{last_em}|{last_p}"
            print('Current state: ', current_state)
            # Have to get less detailed tags so that the comparisons would work properly
            p_tag = content_div.find('p')
            h2_tag = content_div.find('h2')
            em_tag = content_div.find('em')
            next_state = f"{h2_tag.get_text(strip=True)}|{em_tag.get_text(strip=True)}|{p_tag.get_text(strip=True)}"
            print('Next state: ', next_state)

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

        for item in items:
            if item.get('announcement_id', 'N/A') == 0:
                sbp_announcement_state = item.get('announcement_state', 'N/A')
                scrape_course(sbp_announcement_state, 'http://www.acs.uns.ac.rs/sr/sbp', 'sbp')
            elif item.get('announcement_id', 'N/A') == 1:
                iis_announcement_state = item.get('announcement_state', 'N/A')
                scrape_course(iis_announcement_state, 'http://www.acs.uns.ac.rs/sr/ism', 'iis')
            elif item.get('announcement_id', 'N/A') == 2:
                nais_announcement_state = item.get('announcement_state', 'N/A')
                scrape_course(nais_announcement_state, 'http://www.acs.uns.ac.rs/sr/nais', 'nais')
            else:
                print('Error reading data provided by DynamoDB')

    else:
        print('No items found')
