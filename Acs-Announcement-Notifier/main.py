from email.mime.text import MIMEText
import requests
import bs4
import smtplib


def scrape_sbp():
    sbp_url = 'http://www.acs.uns.ac.rs/sr/sbp'
    sbp_last_h2 = '[ASVSP, BP1, SBP] Usmeni ispit - raspored u terminu'
    sbp_last_em = 'Arhitekture sistema velikih skupova podataka - 	10. Februar 2024'
    sbp_last_p = 'Usmeni ispit biće održan u ponedeljak 12. 1. 2024. u laboratoriji MIA2-2 prema priloženom rasporedu.'

    response = requests.get(sbp_url)

    if response.status_code == 200:
        sbp_last_h2, sbp_last_em, sbp_last_p = format_response(response, sbp_last_h2, sbp_last_em, sbp_last_p)
    else:
        print('Error:', response.status_code)


def scrape_iis():
    iis_url = 'http://www.acs.uns.ac.rs/sr/ism'
    iis_last_h2 = 'Raspored polaganja usmenog ispita kod prof. Slavica Kordić za 21.2.2024.'
    iis_last_em = 'Baze podataka 1 - Informacioni inženjering - 	20. Februar 2024'
    iis_last_p = ''

    response = requests.get(iis_url)

    if response.status_code == 200:
        iis_last_h2, iis_last_em, iis_last_p = format_response(response, iis_last_h2, iis_last_em, iis_last_p)
    else:
        print('Error:', response.status_code)


def format_response(response, last_h2, last_em, last_p):
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
            # Radi prikaza samo treba fromatirati, ako bude i bilo neophodno da se bilo sta prikaze
            print(em_tag.get_text(strip=True))
        else:
            print('No <em> tag found within the <div>')

        if p_tag:
            print(p_tag.get_text(strip=True))
        else:
            print('No <p> tag found within the <div>')
        # Pitanje je da li treba i prilog recimo dodati, mozda da se pristupi direktno sa mejla?

        if (h2_tag.get_text(strip=True) != last_h2 or em_tag.get_text(strip=True) != last_em or
                p_tag.get_text(strip=True) != last_p):
            email_subject = 'ACS-Announcement'
            email_body = f'{h2_tag.get_text(strip=True)}<br>{em_tag.get_text(strip=True)}<br><br>{p_tag.get_text(strip=True)}'
            send_email(email_subject, email_body.encode('utf-8'))
            print('Email sent')
            return h2_tag.get_text(strip=True), em_tag.get_text(strip=True), p_tag.get_text(strip=True)
        else:
            print('There are no new announcements')
    else:
        print('No <div> found')


def send_email(subject, body):
    msg = MIMEText(body, 'html', 'utf-8')

    msg['Subject'] = subject
    msg['From'] = 'acs.announcement@gmail.com'
    msg['To'] = 'vule.dok@gmail.com'

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('acs.announcement@gmail.com', 'bgpo jzev azpz brco')
        server.sendmail('acs.announcement@gmail.com', 'vule.dok@gmail.com', msg.as_string())


if __name__ == "__main__":
    #scrape_sbp()
    scrape_iis()
