from random import choice
from googletrans import Translator
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from strsimpy.cosine import Cosine
import pymongo
import createLibrary
import random

myClient: object
myBotData: object
myBookList: object
myCommonList: object
myUserList: object


# 判斷是否為中文
def is_all_chinese(text):
    for _char in text:
        if not '\u4e00' <= _char <= '\u9fa5':
            return False
    return True


def connect():
    global myClient, myBotData, myBookList, myCommonList, myUserList
    try:
        myClient = pymongo.MongoClient("mongodb://root:ltlab35316@140.115.53.196:27017/")

        myBotData = myClient.Chatbot
        myBookList = myBotData.bookList
        myCommonList = myBotData.commonList
        myUserList = myBotData.UserTable
    except Exception as e:
        print(e)

    return myBookList, myCommonList, myClient, myUserList


# 詢問座號
def user_login():
    print("START")
    response = '哈囉！請先告訴我你的班級和座號唷！'
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }
    }}
    return response_dict


# 詢問書名
def start_chat(req):
    print("START")
    if 'User_second_check' in req['session']['params'].keys():
        second_check = req['session']['params']['User_second_check']
    else:
        second_check = False
    if second_check:
        response = ''
    else:
        user_id = req['session']['params']['User_id']
        connect()
        book_record = ''
        find_condition = {'type': 'common_start'}
        find_result = myCommonList.find_one(find_condition)
        response = choice(find_result['content'])
        # 取得該使用者紀錄
        if list(myUserList.find()):
            user_exist = myUserList.find_one({"User_id": user_id})
            if user_exist is not None:
                find_condition = {'type': 'common_combine'}
                find_result = myCommonList.find_one(find_condition)
                allBook = list(user_exist["BookTalkSummary"].keys())
                for i in range(len(allBook)):
                    if i > 0:
                        book_record += choice(find_result['content']) + allBook[i].replace("_", " ")
                    else:
                        book_record += allBook[i].replace("_", " ")
                find_condition = {'type': 'common_registered'}
                find_result = myCommonList.find_one(find_condition)
                response = choice(find_result['content']).replace('X', book_record)

    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }}
    }
    print(response)
    return response_dict


def check_book(req):
    print('CHECK')
    second_check = True
    userSay = req['intent']['query']
    user_id = req['session']['params']['User_id']
    connect()
    if 'User_second_match' in req['session']['params'].keys():
        second_match = req['session']['params']['User_second_match']
    else:
        second_match = False
    if second_match:
        response_dict = {"scene": {
            "next": {
                'name': 'Match_book'
            }
        },
            "session": {
                "params": {
                    'User_second_check': second_check,
                    'User_second_match': second_match
                }
            }}
    else:
        if is_all_chinese(userSay):
            # 若輸入全中文
            find_condition = {'bookNameTranslated': {"$regex": userSay}}
        else:
            find_condition = {'bookName': {"$regex": userSay, "$options": 'i'}}
        find_result_cursor = myBookList.find(find_condition)
        print(find_result_cursor.count())
        if find_result_cursor.count() != 0:
            if find_result_cursor.count() == 1:
                book_match = True
                response_dict = {"scene": {
                    "next": {
                        'name': 'Match_book'
                    }},
                    "session": {
                        "params": {
                            'User_say': userSay,
                            'User_id': user_id,
                            'User_book': find_result_cursor[0]['bookName'],
                            'User_bookMatch': book_match,
                            'User_second_check': second_check,
                            'User_second_match': second_match
                        }
                    }
                }
            else:
                allBook = ''
                for index in range(find_result_cursor.count()):
                    if index == 0:
                        allBook += find_result_cursor[index]['bookName']
                    else:
                        allBook += "、" + find_result_cursor[index]['bookName']
                print(allBook)
                response = '我有看過' + allBook + " 你是在指哪一本故事呢?"
                second_match = True
                response_dict = {"prompt": {
                    "firstSimple": {
                        "speech": response,
                        "text": response
                    }},
                    "session": {
                        "params": {
                            'User_second_match': second_match
                        }
                    }
                }

        else:
            book_match = False
            response_dict = {"scene": {
                "next": {
                    'name': 'Match_book'
                }
            },
                "session": {
                    "params": {
                        'User_bookMatch': book_match,
                        'User_second_check': second_check,
                        'User_second_match': second_match
                    }
                }}
    return response_dict


# 確認書本是否有紀錄
def match_book(req):
    print('Match_record')
    second_match = req['session']['params']['User_second_match']
    record_search = False
    book_match = req['session']['params']['User_bookMatch']
    userSay = req['intent']['query']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    check_Match = False
    connect()
    response = ''
    record_list = []
    match_verb = []
    match_entity = []
    input_sentence = 0
    bookName = ''
    firstTime = True
    double_check = False
    recorded = False
    user_id = req['session']['params']['User_id']
    state = False

    if second_match:
        if is_all_chinese(userSay):
            find_condition = {'bookNameTranslated': userSay}
        else:
            find_condition = {'bookName': userSay}
        find_result_cursor = myBookList.find_one(find_condition)
        if find_result_cursor is not None:
            record_search = True
            bookName = find_result_cursor['bookName']
            print(find_result_cursor)
        else:
            find_common = {'type': 'common_book_F'}
            find_common_result = myCommonList.find_one(find_common)
            response = choice(find_common_result['content'])
    else:
        if book_match:
            # 比對成功
            record_search = True
            bookName = req['session']['params']['User_book']
            print(bookName)
        else:
            # 比對失敗
            find_common = {'type': 'common_book_F'}
            find_common_result = myCommonList.find_one(find_common)
            response = choice(find_common_result['content'])

    if record_search:
        # 比對成功
        check_Match = True

        nowBook = myClient[bookName.replace(' ', '_')]
        myVerbList = nowBook['VerbTable']
        myDialogList = nowBook['S_R_Dialog']
        dialog_index = myDialogList.find().count()
        if dialog_index == 0:
            dialog_id = 0
        else:
            dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
        find_common = {'type': 'common_book_T'}
        find_common_result = myCommonList.find_one(find_common)
        response = choice(find_common_result['content'])
        result = ''
        # 取得書本紀錄
        if list(myUserList.find()):
            user_data_load = myUserList.find_one({"User_id": user_id})
            # 確認有該本書
            if user_data_load is not None and bookName in user_data_load["BookTalkSummary"].keys():
                # 書本狀態紀錄為已完成
                if user_data_load["BookTalkSummary"][bookName]["Finish"]:
                    find_condition = {'type': 'common_finished_T'}
                    find_result = myCommonList.find_one(find_condition)
                    response = choice(find_result['content'])
                    check_Match = False
                else:
                    # 抓出過去的故事資料
                    input_sentence = user_data_load["BookTalkSummary"][bookName]["Input_count"]
                    record_list = user_data_load["BookTalkSummary"][bookName]["Sentence_id_list"]
                    match_entity = user_data_load["BookTalkSummary"][bookName]["Entity_list"]
                    match_verb = user_data_load["BookTalkSummary"][bookName]["Verb_list"]
                    find_common_combine = {'type': 'common_combine'}
                    common_combine = myCommonList.find_one(find_common_combine)
                    if list(record_list):
                        temp_list = record_list[-3:]
                        recorded = True
                        for index in range(len(temp_list)):
                            if index > 0:
                                result += choice(common_combine['content']) + ' ' + \
                                          myVerbList.find_one({"Sentence_Id": int(temp_list[index])})[
                                              "Sentence_translate"]
                            else:
                                result = myVerbList.find_one({"Sentence_Id": int(temp_list[index])})[
                                    "Sentence_translate"]

                        for word in ['。', '，', '！', '“', '”', '：']:
                            result = result.replace(word, '')
                        find_common = {'type': 'common_finished_F'}
                        find_common_result = myCommonList.find_one(find_common)
                        response = choice(find_common_result['content']) + ' ' + result

        # 記錄對話過程
        createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)

    if check_Match:
        second_check = False
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }},
            "scene": {
                "next": {
                    'name': 'Prompt'
                }
            },
            "session": {
                "params": dict(User_say=userSay, User_id=user_id, User_book=bookName, User_record_list=record_list,
                               User_matchEntity=match_entity, User_matchVerb=match_verb, User_inputCount=input_sentence,
                               User_noMatch=0, User_First_bool=firstTime, User_doubleCheck=double_check,
                               User_recorded=recorded, User_state=state, User_second_check=second_check)}
        }
    else:
        second_match = False
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }
        },
            "scene": {
                "next": {
                    'name': 'Check_book'
                }
        },
            "session": {
                "params": {
                    'User_second_check': second_match
                }}
        }

    print(response)
    return response_dict


# 聊書引導
def prompt(req):
    print("PROMPT")
    userSay = req['intent']['query']
    user_id = req['session']['params']['User_id']
    record_list = req['session']['params']['User_record_list']
    match_entity = req['session']['params']['User_matchEntity']
    match_verb = req['session']['params']['User_matchVerb']
    input_sentence = req['session']['params']['User_inputCount']
    double_check = req['session']['params']['User_doubleCheck']
    recorded = req['session']['params']['User_recorded']
    bookName = req['session']['params']['User_book']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    firstTime = req['session']['params']['User_First_bool']
    connect()

    nowBook = myClient[bookName.replace(' ', '_')]
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    # 曾經有紀錄
    if recorded:
        find_common = {'type': 'common_repeat'}
        find_common_result = myCommonList.find_one(find_common)
        response = choice(find_common_result['content'])
        # 記錄對話過程
        createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    elif firstTime:
        find_common = {'type': 'common_prompt'}
        find_common_result = myCommonList.find_one(find_common)
        response = choice(find_common_result['content'])
        # 記錄對話過程
        createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    else:
        response = ''

    recorded = False
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }
    },
        "session": {
            "params": dict(User_say=userSay, User_id=user_id, User_book=bookName, User_record_list=record_list,
                           User_matchEntity=match_entity, User_matchVerb=match_verb, User_inputCount=input_sentence,
                           User_noMatch=0, User_First_bool=firstTime, User_doubleCheck=double_check,
                           User_recorded=recorded)}
    }

    print(response)
    return response_dict


# 比對故事內容
def evaluate(req, predictor):
    print("EVALUATE")
    firstTime = False
    recorded = req['session']['params']['User_recorded']
    double_check = req['session']['params']['User_doubleCheck']
    input_sentence = req['session']['params']['User_inputCount']
    if 'User_noMatch' in req['session']['params'].keys():
        noMatch_count = req['session']['params']['User_noMatch']
    else:
        noMatch_count = 0
    user_id = req['session']['params']['User_id']
    bookName = req['session']['params']['User_book']
    record_list = req['session']['params']['User_record_list']
    match_entity = req['session']['params']['User_matchEntity']
    match_verb = req['session']['params']['User_matchVerb']
    nowBook = myClient[bookName.replace(' ', '_')]
    myQATable = nowBook['QATable']
    myVerbList = nowBook['VerbTable']
    userSay = req['intent']['query']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    if type(userSay) != str:
        response = '我不太懂你說的耶! 你可以再說一次嗎'
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }},
            "scene": {
                "next": {
                    'name': 'Prompt'
                }
            }
        }
    else:
        nowBook = myClient[bookName.replace(' ', '_')]
        myDialogList = nowBook['S_R_Dialog']
        dialog_index = myDialogList.find().count()
        dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
        input_sentence += 1
        no_match = False
        now_index = []
        repeat_content = []
        response = ''
        response_dict = {}
        stop_words = list(stopwords.words('english'))
        for i in ["yourself", "there", "once", "having", "they", "its", "yours", "itself", "is", "him", "themselves",
                  "are",
                  "we", "these", "your", "his", "me", "were", "her", "himself", "this", "our", "their", "ours", "had",
                  "she", "all", "no", "them", "same", "been", "have", "yourselves", "he", "you", "herself", "has",
                  "myself",
                  "those", "i", "being", "theirs", "my", "against", "it", "she's", 'hers']:
            stop_words.remove(i)
        for i in range(len(stop_words)):
            stop_words[i] = " " + stop_words[i] + " "
        stop_words.extend([' . ', ' , ', '"', ' ! '])
        connect()

        if not double_check:
            # 記錄對話過程
            createLibrary.addDialog(bookName, session_id, dialog_id, 'Student ' + user_id, userSay, time)
            dialog_index = myDialogList.find().count()
            dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1

        translator = Translator()

        now_user_say = userSay
        # 若學生輸入多句則作斷句處理
        userSay_list = userSay.split(' ')
        for say in userSay_list:
            print(say)
            # 將原句翻譯
            while True:
                try:
                    trans_word = translator.translate(say, src='zh-TW', dest="en").text
                    break
                except Exception as e:
                    print(e)

            similarity_sentence = {}
            for word in stop_words:
                post_similarity = trans_word.replace(word, ' ')
            print("USER input:" + str(post_similarity))
            # 使用相似度比對
            all_cursor = myVerbList.find()
            for cursor in all_cursor:
                cosine = Cosine(2)
                s1 = post_similarity
                s2 = cursor['Sentence']
                for word in stop_words:
                    s2 = s2.replace(word, ' ')
                print(s2)
                p1 = cosine.get_profile(s1)
                p2 = cosine.get_profile(s2)
                print('第' + str(cursor['Sentence_Id']) + '句相似度：' + str(cosine.similarity_profiles(p1, p2)))
                value = cosine.similarity_profiles(p1, p2)
                if value >= 0.5:
                    similarity_sentence[cursor['Sentence_Id']] = value
            similarity_sentence = sorted(similarity_sentence.items(), key=lambda x: x[1], reverse=True)
            print('similarity_sentence：' + str(similarity_sentence))

            if list(similarity_sentence):
                # 有相似的句子
                result = predictor.predict(
                    sentence=trans_word
                )
                user_c1 = []
                user_v = []
                user_c2 = []
                v = False
                for j in range(len(result['pos'])):
                    if v == False and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                        if result['words'][j] not in user_c1:
                            user_c1.append(result['words'][j])
                        continue
                    if (result['pos'][j] == 'VERB' and result['predicted_dependencies'][j] != 'aux') or (
                            result['pos'][j] == 'AUX' and result['predicted_dependencies'][j] == 'root'):
                        v = True
                        if result['words'][j] not in user_v:
                            user_v.append(result['words'][j])
                        continue
                    if v == True and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                        if result['words'][j] not in user_c2:
                            user_c2.append(result['words'][j])
                        continue
                # 找出使用者說的話的主動詞
                print('USER輸入中的S:' + str(user_c1) + ',V:' + str(user_v) + ',O:' + str(user_c2))

                # 若使用者輸入中結構不完整 > 依照相似度判斷
                if len(user_c1) == 0 or len(user_v) == 0 or len(user_c2) == 0:
                    no_match = True
                # 都不為空才進行二次確認
                elif len(user_c1) != 0 and len(user_v) != 0 and len(user_c2) != 0:
                    for similarity_index in similarity_sentence:
                        print(similarity_index[0])

                        checkC1 = False
                        checkC2 = False
                        checkVerb = False

                        story_c1 = myVerbList.find_one({"Sentence_Id": similarity_index[0]})['C1']
                        story_v = myVerbList.find_one({"Sentence_Id": similarity_index[0]})['Verb']
                        story_c2 = myVerbList.find_one({"Sentence_Id": similarity_index[0]})['C2']

                        if list(story_c1) and list(story_v) and list(story_c2):
                            # 先比對C1
                            if not checkC1:
                                for word in user_c1:
                                    word_case = [word, word.lower(), word.capitalize()]
                                word_case = list(set(word_case))
                                # word是否在storyC1中
                                for index in word_case:
                                    for c1_index in story_c1:
                                        if c1_index == index:
                                            print(c1_index)
                                            checkC1 = True
                                            if index not in match_entity:
                                                match_entity.append(index)
                                            break
                                    if checkC1:
                                        break
                            # 找V
                            if not checkVerb:
                                word_morphy = []
                                word_case = []
                                for word in user_v:
                                    for i in wordnet._morphy(word, pos='v'):
                                        word_morphy.append(i)
                                for index in word_morphy:
                                    while True:
                                        try:
                                            trans_word_pre = translator.translate(index, src='en', dest="zh-TW").text
                                            trans_word = translator.translate(trans_word_pre, dest="en").extra_data[
                                                'parsed']
                                            if len(trans_word) > 3:
                                                for i in trans_word[3][5][0]:
                                                    if i[0] == 'verb':
                                                        for trans_word_index in i[1]:
                                                            word_case.append(trans_word_index[0])
                                                        break
                                            break
                                        except Exception as translator_error:
                                            print(translator_error)
                                word_case.extend(word_morphy)
                                print(word_case)
                                for index in word_case:
                                    for v_index in story_v:
                                        verb_allResult = wordnet._morphy(v_index, pos='v')
                                        for j in verb_allResult:
                                            if j == index:
                                                print(index)
                                                checkVerb = True
                                                if index not in match_verb:
                                                    match_verb.append(index)
                                                break
                                        if checkVerb:
                                            break
                                    if checkVerb:
                                        break
                            # 找C2
                            if not checkC2:
                                word_case = []
                                for word in user_c2:
                                    # 找同義字
                                    while True:
                                        try:
                                            trans_word_pre = translator.translate(word, src='en', dest="zh-TW").text
                                            trans_word = translator.translate(trans_word_pre, dest="en").extra_data[
                                                'parsed']
                                            if len(trans_word) > 3:
                                                for i in trans_word[3][5][0]:
                                                    if i[0] == 'noun':
                                                        for index in i[1]:
                                                            word_case.append(index[0])
                                                        break
                                            break
                                        except Exception as translator_error:
                                            print(translator_error)
                                    word_case.extend([word.lower(), word.capitalize()])
                                word_case = list(set(word_case))
                                print(word_case)
                                for index in word_case:
                                    for c2_index in story_c2:
                                        if c2_index == index:
                                            print(index)
                                            checkC2 = True
                                            if index not in match_entity:
                                                match_entity.append(index)
                                            break
                                    if checkC2:
                                        break

                            print(str(checkC1) + ',' + str(checkC2) + ',' + str(checkVerb))
                            all_cursor = myVerbList.find()
                            if checkVerb and checkC2 and checkC1:
                                no_match = False
                                if similarity_index[0] not in record_list:
                                    record_list.append(similarity_index[0])
                                now_index.append(similarity_index[0])
                                # 比對成功
                                find_common = {'type': 'common_match_T'}
                                find_common_result = myCommonList.find_one(find_common)
                                response = choice(find_common_result['content'])

                                exist_elaboration = myVerbList.find_one(
                                    {"Sentence_Id": similarity_index[0], "Student_elaboration": {'$exists': True}})
                                if exist_elaboration is not None:
                                    # 若有學生曾輸入過的詮釋 > 回答該句
                                    repeat_content.append(
                                        choice(all_cursor[similarity_index[0]]['Student_elaboration']))
                                else:
                                    result = all_cursor[similarity_index[0]]['Sentence_translate']
                                    for word in ['。', '，', '！', '“', '”', '：']:
                                        result = result.replace(word, ' ')
                                    repeat_content.append(result)

                                # 記錄對話過程
                                createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)

                                response_dict = {"prompt": {
                                    "firstSimple": {
                                        "speech": response,
                                        "text": response
                                    }},
                                    "scene": {
                                        "next": {
                                            'name': 'REPEAT'
                                        }
                                    },
                                    "session": {
                                        "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                                                       User_record_list=record_list, User_matchEntity=match_entity,
                                                       User_matchVerb=match_verb, User_inputCount=input_sentence,
                                                       User_noMatch=noMatch_count, User_First_bool=firstTime,
                                                       User_doubleCheck=double_check, User_recorded=recorded,
                                                       User_nowInput=now_user_say, User_repeatContent=repeat_content, User_nowIndex=now_index)}
                                }
                                break
                            else:
                                no_match = True
                                similarity_sentence.remove(similarity_index)
                        else:
                            no_match = True
            else:
                # 沒有相似的句子
                no_match = True

            if no_match:
                if double_check:
                    response_dict = {"scene": {
                        "next": {
                            'name': 'Elaboration'
                        }
                    },
                        "session": {
                            "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                                           User_record_list=record_list, User_matchEntity=match_entity,
                                           User_matchVerb=match_verb, User_inputCount=input_sentence,
                                           User_noMatch=noMatch_count, User_First_bool=firstTime,
                                           User_doubleCheck=double_check, User_recorded=recorded, User_nowIndex=now_index)}
                    }
                else:
                    all_QA_cursor = myQATable.find()
                    QAMatch = False
                    # 比對QA裡的response
                    if all_QA_cursor.count() > 0:
                        for cursor in all_QA_cursor:
                            cosine = Cosine(2)
                            s1 = userSay
                            s2 = cursor['Response']
                            p1 = cosine.get_profile(s1)
                            p2 = cosine.get_profile(s2)
                            print('QA相似度：' + str(cosine.similarity_profiles(p1, p2)))
                            if cosine.similarity_profiles(p1, p2) >= 0.7:
                                qa_id = cursor['QA_Id']
                                QAMatch = True
                                response_dict = {
                                    "scene": {
                                        "next": {
                                            'name': 'INQUIRE'
                                        }
                                    },
                                    "session": {
                                        "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                                                       User_record_list=record_list, User_matchEntity=match_entity,
                                                       User_matchVerb=match_verb, User_inputCount=input_sentence,
                                                       User_noMatch=noMatch_count, User_First_bool=firstTime,
                                                       User_doubleCheck=double_check, User_recorded=recorded,
                                                       User_qaId=qa_id, User_nowIndex=now_index)}
                                }
                                break
                    if all_QA_cursor is None or not QAMatch:
                        noMatch_count += 1
                        myQAList = nowBook['QATable']
                        qa_id = myQAList.find().count()

                        # 存入比對不到的使用者對話
                        createLibrary.addQuestion(bookName, qa_id, dialog_id - 1, userSay)

                        # 請使用者補充說明
                        find_common = {'type': 'common_match_F'}
                        find_common_result = myCommonList.find_one(find_common)
                        response = choice(find_common_result['content'])

                        double_check = True

                        # 記錄對話過程
                        createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)

                        response_dict = {"prompt": {
                            "firstSimple": {
                                "speech": response,
                                "text": response
                            }},
                            "scene": {
                                "next": {
                                    'name': 'Prompt'
                                }
                            },
                            "session": {
                                "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                                               User_record_list=record_list, User_matchEntity=match_entity,
                                               User_matchVerb=match_verb, User_inputCount=input_sentence,
                                               User_noMatch=noMatch_count, User_First_bool=firstTime,
                                               User_doubleCheck=double_check, User_recorded=recorded, User_nowInput=now_user_say, User_repeatContent=repeat_content)}
                        }

    print(response)
    return response_dict


# 比對正確則覆述使用者說的故事
def repeat(req):
    print("REPEAT")
    bookName = req['session']['params']['User_book']
    nowBook = myClient[bookName.replace(' ', '_')]
    myVerbList = nowBook['VerbTable']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    userSay = req['intent']['query']
    user_id = req['session']['params']['User_id']
    record_list = req['session']['params']['User_record_list']
    match_entity = req['session']['params']['User_matchEntity']
    match_verb = req['session']['params']['User_matchVerb']
    input_sentence = req['session']['params']['User_inputCount']
    double_check = req['session']['params']['User_doubleCheck']
    recorded = req['session']['params']['User_recorded']
    firstTime = req['session']['params']['User_First_bool']
    noMatch_count = req['session']['params']['User_noMatch']
    nowBook = myClient[bookName.replace(' ', '_')]
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    now_user_say = req['session']['params']['User_nowInput']
    response = ''
    now_index = req['session']['params']['User_nowIndex']
    repeat_content = req['session']['params']['User_repeatContent']
    if len(repeat_content) > 1:
        for i in repeat_content:
            response += i + " "
    else:
        response = repeat_content[0]
    confidence = 0
    if len(now_index) == 0:
        sentence_id = ''
    else:
        # elaboration連結回故事ID 並存入故事中的句子作為機器人語料庫
        sentence_id = now_index[0]
        exist_elaboration = myVerbList.find_one(
            {'Sentence_Id': sentence_id, "Student_elaboration": {'$exists': True}})
        if exist_elaboration is not None:
            student_elaboration = myVerbList.find_one({'Sentence_Id': sentence_id})['Student_elaboration']
            if now_user_say not in student_elaboration:
                student_elaboration.append(now_user_say)
        else:
            student_elaboration = [now_user_say]
        newvalues = {"$set": {'Student_elaboration': student_elaboration}}
        myVerbList.update_one({'Sentence_Id': sentence_id}, newvalues)

    if double_check:
        myQAList = nowBook['QATable']
        qa_id = myQAList.find().count() - 1
        createLibrary.addElaboration(bookName, qa_id, now_user_say, confidence, sentence_id)

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    double_check = False

    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }},
        "scene": {
            "next": {
                'name': 'RETRIVE'
            }
        },
        "session": {
            "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                           User_record_list=record_list, User_matchEntity=match_entity, User_matchVerb=match_verb,
                           User_inputCount=input_sentence, User_noMatch=noMatch_count, User_First_bool=firstTime,
                           User_doubleCheck=double_check, User_recorded=recorded, User_nowIndex=now_index)}
    }

    print(response)
    return response_dict


# 接續使用者的下一句
def retrive(req):
    print("RETRIVE")
    go_expand = False
    recorded = req['session']['params']['User_recorded']
    double_check = req['session']['params']['User_doubleCheck']
    firstTime = req['session']['params']['User_First_bool']
    input_sentence = req['session']['params']['User_inputCount']
    user_id = req['session']['params']['User_id']
    record_list = req['session']['params']['User_record_list']
    noMatch_count = req['session']['params']['User_noMatch']
    match_entity = req['session']['params']['User_matchEntity']
    match_verb = req['session']['params']['User_matchVerb']
    userSay = req['session']['params']['User_say']
    bookName = req['session']['params']['User_book']
    nowBook = myClient[bookName.replace(' ', '_')]
    myVerbList = nowBook['VerbTable']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    nowBook = myClient[bookName.replace(' ', '_')]
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    response = ''
    connect()
    now_index = req['session']['params']['User_nowIndex']
    all_cursor = myVerbList.find()
    print(record_list)
    if input_sentence > (all_cursor.count() / 2):
        # 講到的句數超過一半
        go_expand = True
    else:
        if len(now_index) == 0:
            # 沒有新故事
            if len(record_list) == 0:
                # 沒有任何故事就直接講第一句
                find_common = {'type': 'common_return'}
                find_common_result = myCommonList.find_one(find_common)
                result = all_cursor[0]["Sentence_translate"]
                for word in ['。', '，', '！', '“', '”', '：']:
                    result = result.replace(word, ' ')
                response = choice(find_common_result['content']) + ' ' + result
                record_list.append(0)
            else:
                # 依據前次記錄到的句子接續講下一句
                find_condition = {'Sentence_Id': record_list[-1]}
                find_result_cursor = myVerbList.find_one(find_condition)
                story_conj = '故事裡還有提到'
                result = find_result_cursor["Sentence_translate"]
                for word in ['。', '，', '！', '“', '”', '：']:
                    result = result.replace(word, ' ')
                response = story_conj + ' ' + result
                if (record_list[-1]) not in record_list:
                    record_list.append(record_list[-1])
        else:
            # 排序now_index
            now_index = sorted(now_index, reverse=True)
            find_condition = {'Sentence_Id': now_index[0] + 1}
            find_result_next = myVerbList.find_one(find_condition)
            find_common_follow = {'type': 'common_retrieve'}
            result_follow = myCommonList.find_one(find_common_follow)
            find_common_conj = {'type': 'common_conj'}
            result_conj = myCommonList.find_one(find_common_conj)
            story_conj = choice(result_conj['content']) + choice(result_follow['content'])
            result = find_result_next["Sentence_translate"]
            for word in ['。', '，', '！', '“', '”', '：']:
                result = result.replace(word, ' ')
            response = story_conj + ' ' + result
            if (now_index[0] + 1) not in record_list:
                record_list.append(now_index[0] + 1)

    if go_expand:
        state = req['session']['params']['User_state']
        createLibrary.updateUser(user_id, bookName, input_sentence, record_list, match_entity, match_verb, state, noMatch_count)
        response_dict = {
            "scene": {
                "next": {
                    'name': 'Expand'
                }
            },
            "session": {
                "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                               User_record_list=record_list, User_matchEntity=match_entity, User_matchVerb=match_verb,
                               User_inputCount=input_sentence, User_noMatch=noMatch_count, User_First_bool=firstTime,
                               User_doubleCheck=double_check, User_recorded=recorded)}
        }
    else:
        find_common = {'type': 'common_repeat'}
        find_common_result = myCommonList.find_one(find_common)
        response += " " + choice(find_common_result['content'])
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }},
            "scene": {
                "next": {
                    'name': 'Prompt'
                }
            },
            "session": {
                "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                               User_record_list=record_list, User_matchEntity=match_entity, User_matchVerb=match_verb,
                               User_noMatch=noMatch_count, User_First_bool=firstTime, User_doubleCheck=double_check,
                               User_recorded=recorded)}
        }

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)

    print(response)
    state = req['session']['params']['User_state']
    createLibrary.updateUser(user_id, bookName, input_sentence, record_list, match_entity, match_verb, state, noMatch_count)
    return response_dict


# 確認比對到的QA
def inquire(req):
    print('Inquire')
    recorded = req['session']['params']['User_recorded']
    double_check = req['session']['params']['User_doubleCheck']
    input_sentence = req['session']['params']['User_inputCount']
    firstTime = req['session']['params']['User_First_bool']
    user_id = req['session']['params']['User_id']
    record_list = req['session']['params']['User_record_list']
    noMatch_count = req['session']['params']['User_noMatch']
    match_entity = req['session']['params']['User_matchEntity']
    match_verb = req['session']['params']['User_matchVerb']
    userSay = req['session']['params']['User_say']
    bookName = req['session']['params']['User_book']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    nowBook = myClient[bookName.replace(' ', '_')]
    myElaboration = nowBook['Elaboration']
    qa_id = req['session']['params']['User_qaId']
    find_result = {'QA_Id': qa_id}
    result = myElaboration.find_one(find_result)
    nowBook = myClient[bookName.replace(' ', '_')]
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    now_index = req['session']['params']['User_nowIndex']

    find_common = {'type': 'common_QA'}
    find_common_result = myCommonList.find_one(find_common)
    find_common_2 = {'type': 'common_repeat'}
    find_common_result_2 = myCommonList.find_one(find_common_2)
    response = choice(find_common_result['content']) + " " + result['Elaboration'] + "，" + choice(
        find_common_result_2['content'])
    if result['Sentence_Id'] != '':
        record_list.append(result['Sentence_Id'])
        now_index.append(result['Sentence_Id'])

    state = req['session']['params']['User_state']
    createLibrary.updateUser(user_id, bookName, input_sentence, record_list, match_entity, match_verb, state, noMatch_count)
    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)

    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }},
        "scene": {
            "next": {
                'name': 'PROMPT'
            }
        },
        "session": {
            "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                           User_record_list=record_list, User_matchEntity=match_entity, User_matchVerb=match_verb,
                           User_inputCount=input_sentence, User_noMatch=noMatch_count, User_First_bool=firstTime,
                           User_doubleCheck=double_check, User_recorded=recorded, User_nowIndex=now_index)}
    }
    print(response)
    return response_dict


# 增加新的Elaboration
def addElaboration(req):
    print('Elaboration')
    double_check = False
    recorded = req['session']['params']['User_recorded']
    firstTime = req['session']['params']['User_First_bool']
    user_id = req['session']['params']['User_id']
    userSay = req['intent']['query']
    bookName = req['session']['params']['User_book']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    noMatch_count = req['session']['params']['User_noMatch']
    input_sentence = req['session']['params']['User_inputCount']
    record_list = req['session']['params']['User_record_list']
    match_entity = req['session']['params']['User_matchEntity']
    match_verb = req['session']['params']['User_matchVerb']
    response = ''
    nowBook = myClient[bookName.replace(' ', '_')]
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1

    # 暫定信心值
    confidence = 0
    sentence_id = ''
    myQAList = nowBook['QATable']
    qa_id = myQAList.find().count() - 1
    createLibrary.addElaboration(bookName, qa_id, userSay, confidence, sentence_id)

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'Student ' + user_id, userSay, time)

    if noMatch_count == 3:
        noMatch_count = 0
        response_dict = {
            "scene": {
                "next": {
                    'name': 'RETRIVE'
                }
            },
            "session": {
                "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                               User_record_list=record_list, User_matchEntity=match_entity, User_matchVerb=match_verb,
                               User_inputCount=input_sentence, User_noMatch=noMatch_count, User_First_bool=firstTime,
                               User_doubleCheck=double_check, User_recorded=recorded)}
        }
    else:
        find_common = {'type': 'common_elaboration'}
        find_common_result = myCommonList.find_one(find_common)
        response = choice(find_common_result['content']) + " " + userSay

        find_common_2 = {'type': 'common_repeat'}
        find_common_result_2 = myCommonList.find_one(find_common_2)
        response = response + " " + choice(find_common_result_2['content'])
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }},
            "scene": {
                "next": {
                    'name': 'PROMPT'
                }
            }
        }

    # 記錄對話過程
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)

    print(response)
    return response_dict


# 學生心得回饋
def expand(req, senta):
    print("Expand")
    state = True
    recorded = req['session']['params']['User_recorded']
    firstTime = req['session']['params']['User_First_bool']
    user_id = req['session']['params']['User_id']
    noMatch_count = req['session']['params']['User_noMatch']
    input_sentence = req['session']['params']['User_inputCount']
    record_list = req['session']['params']['User_record_list']
    match_entity = req['session']['params']['User_matchEntity']
    match_verb = req['session']['params']['User_matchVerb']
    double_check = req['session']['params']['User_doubleCheck']
    bookName = req['session']['params']['User_book']
    userSay = req['intent']['query']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    nowBook = myClient[bookName.replace(' ', '_')]
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    if 'User_expand' in req['session']['params'].keys():
        expand_user = req['session']['params']['User_expand']
    else:
        expand_user = False
    if not expand_user:
        find_common_expand = {'type': 'common_expand'}
        common_result_expand = myCommonList.find_one(find_common_expand)
        find_common = {'type': 'common_like'}
        find_result = myCommonList.find_one(find_common)
        response = "\n" + choice(common_result_expand['content']) + ' ' + choice(find_result['content'])
        expand_user = True
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }},
            'session': {
                'params': {
                    'User_expand': expand_user
                }
            }
        }
    else:
        # Senta情感分析
        input_dict = {"text": [userSay]}
        results = senta.sentiment_classify(data=input_dict)
        if results[0]['sentiment_key'] == "positive" and results[0]['positive_probs'] >= 0.76:
            # 接續詢問使用者喜歡故事的原因
            find_common = {'type': 'common_like_response'}
            find_common2 = {'type': 'common_like_expand'}
            find_result = myCommonList.find_one(find_common)
            find_result2 = myCommonList.find_one(find_common2)
            response = choice(find_result['content']) + ' ' + choice(find_result2['content'])
            suggest_like = True
        else:
            find_common = {'type': 'common_like_F_expand'}
            find_result = myCommonList.find_one(find_common)
            response = choice(find_result['content'])
            suggest_like = False
        expand_user = False
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }},
            "scene": {
                "next": {
                    'name': 'Feedback'
                }
            },
            "session": {
                "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                               User_record_list=record_list, User_matchEntity=match_entity, User_matchVerb=match_verb,
                               User_inputCount=input_sentence, User_noMatch=noMatch_count, User_First_bool=firstTime,
                               User_doubleCheck=double_check, User_recorded=recorded, User_sentiment=suggest_like,
                               User_state=state,User_expand=expand_user)}
        }

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    print(response)
    return response_dict


# 從資料庫中取資料做為機器人給予學生之回饋
def feedback(req):
    print('Feedback')
    double_check = req['session']['params']['User_doubleCheck']
    recorded = req['session']['params']['User_recorded']
    firstTime = req['session']['params']['User_First_bool']
    noMatch_count = req['session']['params']['User_noMatch']
    input_sentence = req['session']['params']['User_inputCount']
    record_list = req['session']['params']['User_record_list']
    match_entity = req['session']['params']['User_matchEntity']
    match_verb = req['session']['params']['User_matchVerb']
    userSay = req['intent']['query']
    user_id = req['session']['params']['User_id']
    bookName = req['session']['params']['User_book']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    nowBook = myClient[bookName.replace(' ', '_')]
    myFeedback = nowBook['Feedback']
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'Student ' + user_id, userSay, time)
    find_common = {'type': 'common_feedback'}
    find_result = myCommonList.find_one(find_common)
    find_feedback_student = {'type': 'common_feedback_student'}
    result_feedback_student = myCommonList.find_one(find_feedback_student)
    suggest_like = req['session']['params']['User_sentiment']
    find_like = {'Sentiment': suggest_like}
    result_like = myFeedback.find(find_like)
    if result_like.count() == 0:
        response = '哦！謝謝你跟我分享！'
    else:
        if result_like.count() > 2:
            choose_number = random.sample(range(0, result_like.count() - 1), 2)
            response = choice(find_result['content']) + " " + result_like[choose_number[0]]['Content'] + "，" + choice(
                result_feedback_student['content']) + " " + result_like[choose_number[1]]['Content']
        elif result_like.count() == 2:
            response = choice(find_result['content']) + " " + result_like[0]['Content'] + "，" + choice(
                result_feedback_student['content']) + " " + result_like[1]['Content']
        else:
            choose_number = 0
            response = choice(find_result['content']) + " " + result_like[choose_number]['Content']
    response += '\n'
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }},
        "scene": {
            "next": {
                'name': 'Suggest'
            }
        },
        "session": {
            "params": dict(User_say=userSay, User_id=user_id, User_book=bookName,
                           User_record_list=record_list, User_matchEntity=match_entity, User_matchVerb=match_verb,
                           User_inputCount=input_sentence, User_noMatch=noMatch_count, User_First_bool=firstTime,
                           User_doubleCheck=double_check, User_recorded=recorded, User_sentiment=suggest_like)}
    }
    createLibrary.addFeedback(user_id, bookName, suggest_like, userSay)
    # 記錄對話過程
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    print(response)
    return response_dict


# 依據學生喜好建議其他書籍
def suggestion(req):
    print("Suggestion")
    connect()
    suggest_like = req['session']['params']['User_sentiment']
    bookName = req['session']['params']['User_book']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    nowBook = myClient[bookName.replace(' ', '_')]
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    suggest_book = {}
    stop_words = list(stopwords.words('english'))
    for i in range(len(stop_words)):
        stop_words[i] = " " + stop_words[i] + " "
    stop_words.extend(['.', ',', '"', '!', "'s", '?'])
    # 與資料庫中其他書的內容作相似度比對
    sample_book = myBookList.find_one({'bookName': bookName.replace('_', ' ')})['story_content']
    comparison_book = myBookList.find({'bookName': {'$ne': bookName.replace('_', ' ')}})
    for word in stop_words:
        sample_book = sample_book.replace(word, ' ')
    for book in comparison_book:
        for word in stop_words:
            story_content = book['story_content'].replace(word, ' ')
        cosine = Cosine(2)
        p1 = cosine.get_profile(sample_book.replace('   ', ' ').replace('  ', ' '))
        p2 = cosine.get_profile(story_content.replace('   ', ' ').replace('  ', ' '))
        suggest_book[book['bookName']] = cosine.similarity_profiles(p1, p2)
    find_condition = {'type': 'common_combine'}
    result_combine = myCommonList.find_one(find_condition)
    like_str = ''
    if suggest_like:
        # 學生喜歡則列出前3高相似度的書籍
        find_common = {'type': 'common_like_T'}
        find_result = myCommonList.find_one(find_common)
        sort_suggest_book = sorted(suggest_book.items(), key=lambda x: x[1], reverse=True)
    else:
        find_common = {'type': 'common_like_F'}
        find_result = myCommonList.find_one(find_common)
        sort_suggest_book = sorted(suggest_book.items(), key=lambda x: x[1], reverse=False)
    for index in range(len(sort_suggest_book[0:3])):
        if index > 0:
            like_str += choice(result_combine['content']) + sort_suggest_book[index][0]
        else:
            like_str += sort_suggest_book[index][0]
    response = choice(find_result['content']).replace('XX', like_str)

    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }}
    }
    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    print(response)
    return response_dict


def exit_system(req):
    print("Exit")
    if 'User_id' in req['session']['params'].keys() and 'User_book' in req['session']['params'].keys():
        createLibrary.updateUser(req['session']['params']['User_id'], req['session']['params']['User_book'],
                                 req['session']['params']['User_inputCount'],
                                 req['session']['params']['User_record_list'],
                                 req['session']['params']['User_matchEntity'],
                                 req['session']['params']['User_matchVerb'], req['session']['params']['User_state'], req['session']['params']['User_noMatch'])


if __name__ == '__main__':
    print(0)
