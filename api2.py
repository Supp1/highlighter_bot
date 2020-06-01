import requests
import telebot
from flask import Flask
from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker

# WEBHOOK_LISTEN = "0.0.0.0"
# WEBHOOK_PORT = 8443
CLIENT_ID = 'gp762nuuoqcoxypju8c569th9wz7q5'
TWITCH_AUTH_TOKEN = 'Bearer 984zuraizg1z1ppuwwqva7kkxrqso6'

API_TOKEN = '1231129772:AAFxVQsBCZRqs-VnK3sjwUTAJ_7lWXli0HA'
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///static/db/highliter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

Session = sessionmaker()
Session.configure(bind=db.engine)
session = Session()


class HighlightClip(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    url = db.Column(db.String(500))
    state = db.Column(db.Boolean())

    def __repr__(self):
        return f'<Clip {self.id}, {self.url}, {self.state}'


class TgUser(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    chat_id = db.Column(db.Integer)

    def __repr__(self):
        return f'<Clip {self.id}, {self.url}, {self.state}'


@app.route('/save_urls', methods=['POST'])
def save_url():
    request_body_dict = request.json
    clip_url = request_body_dict['url']
    clip = HighlightClip(url=clip_url, state=False)
    db.session.add(clip)
    db.session.commit()
    # slug = clip_url.split('/')[3]
    # url, title = retrieve_mp4_data(slug)
    # output_path = './static/clips'
    # urllib.request.urlretrieve(url, f"{output_path}/{title}.mp4")
    # send_clips_url()
    # send_clips_video(title + '.mp4')
    send_clips_url()
    return app.response_class(
        response='OK',
        status=200,
        mimetype='application/json'
    )


@app.route('/test', methods=['GET'])
def test():
    print('asd')
    return 'HELLO WORLD'


@app.route('/<token>', methods=['POST'])
# process only requests with correct bot token
def handle(token):
    if token == bot.token:
        request_body_dict = request.json
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return app.response_class(
            response='OK',
            status=200,
            mimetype='application/json'
        )
    else:
        return app.response_class(
            response='Error',
            status=403,
            mimetype='application/json'
        )


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Hi, i am Highlighter bot. ")


@bot.message_handler(commands=['enable'])
def enable_subscribe(message):
    if TgUser.query.filter_by(chat_id=message.chat.id).first() is not None:
        bot.send_message(message.chat.id, "You have been subscribed already")
        return
    user = TgUser(chat_id=message.chat.id)
    db.session.add(user)
    db.session.commit()
    bot.send_message(message.chat.id, "Success")


@bot.message_handler(commands=['disable'])
def disable_subscribe(message):
    if TgUser.query.filter_by(chat_id=message.chat.id).first() is None:
        bot.send_message(message.chat.id, "You haven't subscribed yet")
        return
    TgUser.query.filter(TgUser.chat_id == message.chat.id).delete()
    db.session.commit()
    bot.send_message(message.chat.id, "Success")


# @bot.message_handler(commands=["help"])
# def send_help(message):
#     bot.send_message(message.chat.id, '', parse_mode="Markdown")

def retrieve_mp4_data(slug):
    clip_info = requests.get(
        "https://api.twitch.tv/helix/clips?id=" + slug,
        headers={"Client-ID": CLIENT_ID, "Authorization": TWITCH_AUTH_TOKEN}).json()
    thumb_url = clip_info['data'][0]['thumbnail_url']
    title = clip_info['data'][0]['title']
    slice_point = thumb_url.index("-preview-")
    mp4_url = thumb_url[:slice_point] + '.mp4'
    return mp4_url, title


def send_clips_url():
    users = TgUser.query.all()
    clip = HighlightClip.query.order_by(HighlightClip.id.desc()).first()
    for user in users:
        bot.send_message(user.chat_id, clip.url)


def send_clips_video(name):
    users = TgUser.query.all()
    for user in users:
        bot.send_video(user.chat_id, './static/clips/' + name)


if __name__ == '__main__':
    app.run(debug=True)
    db.create_all()
