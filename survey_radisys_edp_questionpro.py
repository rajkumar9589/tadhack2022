from flask import Flask, request
import json
import requests
import collections
from deep_translator import GoogleTranslator


app = Flask(__name__)

question_id_dict = {}
question_text_dict = collections.defaultdict(dict)
answer_id_dict = {}
num_questions = 0
survey_id = <questionpro_survey_id>
user_response_dict = collections.defaultdict(dict)
user_last_question_dict ={}

languages = ['french']

def translate_to_lang(text, language):
    # translator= Translator(from_lang="english",to_lang=language)
    # translation = translator.translate(text)
    # return translation
    translated = GoogleTranslator(source='english', target=language).translate(text)
    return translated


def translate_from_lang(text, language):
    # translator= Translator(from_lang=language,to_lang="english")
    # translation = translator.translate(text)
    # return translation
    translated = GoogleTranslator(source=language,target='english').translate(text)
    return translated



@app.route('/api/survey/answers',methods=['POST'])
def edp_submit_answer():
    args = request.args
    print('Submit Answer')
    answer = args.get("answer")
    user = args.get("user")
    language = args.get("language")
    current_question = user_last_question_dict[user]
    if (language == 'fr-FR'):
        answer_text = translate_from_lang(answer, 'french')
    else:
        answer_text = answer
    answer_text.replace("?","")
    user_response_dict[user][current_question] = answer_text

    if (current_question == num_questions):
        create_response(user)
        del user_response_dict[user]
        del user_last_question_dict[user]


    print("Response Dict {}".format(user_response_dict))

    return 'Hello World'

@app.route('/api/survey/questions',methods=['GET'])
def edp_get_question():
    print('Number of Questions are {}'.format(num_questions))
    args = request.args
    language = args.get("language")
    user = args.get("user")
    if user in user_last_question_dict:
        last_question = user_last_question_dict[user]
    else:
        last_question = 0;

    current_question = last_question + 1
    if (language == 'fr-FR'):
        current_question_text = question_text_dict[current_question]['french']
    else:
        current_question_text = question_text_dict[current_question]['english']

    user_last_question_dict[user] = current_question

    print('User: {} Question Number: {} Text: {}',user, current_question, current_question_text)
    return current_question_text

def get_questions (survey_id):
   url = 'https://api.questionpro.com/a/api/v2/surveys/{}/questions'.format(survey_id)
   questions = requests.get(url,params={'apiKey':'<questionpro_api_key>'})
   str_response = questions.content.decode("UTF-8")
   json_response = json.loads(str_response)
   #print(json_response)
   return json_response


def get_answer(survey_id, question_id):
   url = 'https://api.questionpro.com/a/api/v2/surveys/{}/questions/{}/answers'.format(survey_id,question_id)
   answers = requests.get(url,params={'apiKey':'<questionpro_api_key>'})
   str_response = answers.content.decode("UTF-8")
   json_response = json.loads(str_response)
   #print(json_response)
   answer_id = json_response['response'][0]['answerID']
   return answer_id

def create_response(user):
    api_key = '<questionpro_api_key>'
    data_list = list()

    url = "https://api.questionpro.com/a/api/v2/surveys/{0}/responses?apiKey={1}".format(
        survey_id, api_key
    )

    for orderNumber in question_id_dict.keys():
        data = dict()
        data['questionID'] = question_id_dict[orderNumber]
        data['answerValues'] = [
            {
                "answerID": answer_id_dict[orderNumber],
                "value": {
                    "text": user_response_dict[user][orderNumber]
                }
            }
        ]

        data_list.append(data)

    print(data_list)
    response  = requests.post(url, json={'responseSet': data_list})

    print(response)

# main driver function
if __name__ == '__main__':

    json_response = get_questions(survey_id)
    num_questions = len(json_response['response'])
    print('Number of Questions are {}'.format(num_questions))

    for i in range(num_questions):
        orderNumber = json_response['response'][i]['orderNumber']
        question_id = json_response['response'][i]['questionID']
        question_text =  json_response['response'][i]['rows'][0]['text']
        question_id_dict[orderNumber] = question_id
        question_text_dict[orderNumber]['english'] = question_text
        answer_id_dict[orderNumber] = get_answer(survey_id,question_id)

        for each in languages:
            question_text_dict[orderNumber][each] = translate_to_lang(question_text, each)
        answer_id_dict[orderNumber] = get_answer(survey_id,question_id)

    print('Question ID Dict {}'.format(question_id_dict))
    print('Question Text Dict {}'.format(question_text_dict))
    print('Answer ID Dict {}'.format(answer_id_dict))

    app.run()
