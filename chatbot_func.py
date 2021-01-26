from random import choice
from googletrans import Translator
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from strsimpy.cosine import Cosine
import pymongo
import createLibrary

myClient: object
myBotData: object
myBookList: object
myCommonList: object
myVerbList: object
allDialog: object
myQATable: object
myElaboration: object
myUserList: object

bookName = ''
record_list = []
repeat_content = []
match_entity = []
match_verb = []
user_id = ''
now_index = []
now_user_say = ''
firstTime: bool
double_check: bool
dialog_id: int
qa_id: int
second_login: False
state: False
expand_user = False
book_match = False
second_check = False
second_match = False
suggest_like = False


# 判斷是否為中文
def is_all_chinese(text):
    for _char in text:
        if not '\u4e00' <= _char <= '\u9fa5':
            return False
    return True


def connect():
    global myClient, myBotData, myBookList, myCommonList, myUserList
    try:
        myClient = pymongo.MongoClient("mongodb://140.115.53.196:27017/")

        myBotData = myClient.Chatbot
        myBookList = myBotData.bookList
        myCommonList = myBotData.commonList
        myUserList = myBotData.UserTable
    except Exception as e:
        print(e)

    return myBookList, myCommonList, myClient, myUserList


# 詢問座號
def user_login(req):
    print("START")
    response = '哈囉~請先告訴我你的座號唷~'
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
    global user_id, second_check
    user_id = req['intent']['query']
    connect()
    book_record = ''
    if second_check:
        response = ''
    else:
        find_condition = {'type': 'common_start'}
        find_result = myCommonList.find_one(find_condition)
        response = choice(find_result['content'])
        # 取得該使用者紀錄
        if list(myUserList.find()):
            user_exist = myUserList.find_one({"User_id": 'Student ' + user_id})
            if user_exist is not None:
                find_condition = {'type': 'commonmyUserList_combine'}
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
    global book_match, bookName, second_match, second_check
    second_check = True
    userSay = req['intent']['query']
    connect()
    if second_match:
        response_dict = {"scene": {
            "next": {
                'name': 'Match_book'
            }
        }}
    else:
        if is_all_chinese(userSay):
            # 若輸入全中文
            find_condition = {'bookNameTranslate': {"$regex": userSay}}
        else:
            find_condition = {'bookName': {"$regex": userSay, "$options": 'i'}}
        find_result_cursor = myBookList.find(find_condition)
        print(find_result_cursor.count())
        if find_result_cursor.count() != 0:
            if find_result_cursor.count() == 1:
                book_match = True
                bookName = find_result_cursor[0]['bookName'].replace(' ', '_')
                response_dict = {"scene": {
                    "next": {
                        'name': 'Match_book'
                    }
                }}
            else:
                allBook = ''
                for index in range(find_result_cursor.count()):
                    if index == 0:
                        allBook += find_result_cursor[index]['bookName']
                    else:
                        allBook += "、" + find_result_cursor[index]['bookName']
                print(allBook)
                response = '我有看過'+allBook+" 你是在指哪一本故事呢?"
                response_dict = {"prompt": {
                    "firstSimple": {
                        "speech": response,
                        "text": response
                    }
                }}
                second_match = True
        else:
            book_match = False
            response_dict = {"scene": {
                "next": {
                    'name': 'Match_book'
                }
            }}

    return response_dict


# 確認書本是否有紀錄
def match_book(req):
    print('Match_record')
    global bookName, myVerbList, allDialog, firstTime, dialog_id, qa_id, myQATable, myElaboration, double_check, second_login, record_list, match_entity, match_verb, state, book_match, second_match, second_check
    record_search = False
    userSay = req['intent']['query']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    check_Match = False
    connect()
    response = ''

    if second_match:
        if is_all_chinese(userSay):
            find_condition = {'bookNameTranslate': userSay}
        else:
            find_condition = {'bookName': userSay}
        find_result_cursor = myBookList.find_one(find_condition)
        if find_result_cursor is not None:
            record_search = True
            bookName = find_result_cursor['bookName'].replace(' ', '_')
            print(find_result_cursor)
        else:
            find_common = {'type': 'common_book_F'}
            find_common_result = myCommonList.find_one(find_common)
            response = choice(find_common_result['content'])
    else:
        if book_match:
            # 比對成功
            record_search = True
            print(bookName)
        else:
            # 比對失敗
            find_common = {'type': 'common_book_F'}
            find_common_result = myCommonList.find_one(find_common)
            response = choice(find_common_result['content'])

    if record_search:
        # 比對成功
        check_Match = True
        firstTime = True
        double_check = False
        dialog_id = 0
        qa_id = 0
        state = False
        second_login = False

        nowBook = myClient[bookName]
        myVerbList = nowBook['VerbTable']
        allDialog = nowBook['S_R_Dialog']
        myQATable = nowBook['QATable']
        myElaboration = nowBook['Elaboration']

        find_common = {'type': 'common_book_T'}
        find_common_result = myCommonList.find_one(find_common)
        response = choice(find_common_result['content'])

        # 記錄對話過程
        createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
        dialog_id += 1

        # 取得書本紀錄
        if list(myUserList.find()):
            user_data_load = myUserList.find_one({"User_id": 'Student ' + user_id})
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
                    record_list = user_data_load["BookTalkSummary"][bookName]["Sentence_id_list"]
                    match_entity = user_data_load["BookTalkSummary"][bookName]["Entity_list"]
                    match_verb = user_data_load["BookTalkSummary"][bookName]["Verb_list"]
                    if list(record_list):
                        second_login = True
                        if len(record_list) > 1:
                            if len(record_list) == 1:
                                result = myVerbList.find_one({"Sentence_id": int(record_list[0])})["Sentence_translate"]
                            elif len(record_list) == 2:
                                result = myVerbList.find_one({"Sentence_id": int(record_list[0])})["Sentence_translate"] + '、' + myVerbList.find_one({"Sentence_id": int(record_list[1])})["Sentence_translate"]
                            else:
                                result = myVerbList.find_one({"Sentence_id": int(record_list[-3])})["Sentence_translate"]
                                for i in range(len(record_list)):
                                    if i < 3:
                                        result += '、' + myVerbList.find_one({"Sentence_id": int(record_list[i-2])})["Sentence_translate"]
                        else:
                            result = myVerbList.find_one({"Sentence_id": int(record_list[0])})["Sentence_translate"]

                        for word in ['。', '，', '！']:
                            result = result.replace(word, '')
                        find_common = {'type': 'common_finished_F'}
                        find_common_result = myCommonList.find_one(find_common)
                        response = choice(find_common_result['content']) + result

        # 記錄對話過程
        createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
        dialog_id += 1

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
            }
        }
    else:
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
            }
        }
        second_match = False

    print(response)
    return response_dict


# 聊書引導
def prompt(req):
    print("PROMPT")
    global dialog_id, second_login, state
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    connect()
    # 曾經有紀錄
    if second_login:
        find_common = {'type': 'common_repeat'}
        find_common_result = myCommonList.find_one(find_common)
        response = choice(find_common_result['content'])
        # 記錄對話過程
        createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
        dialog_id += 1
    elif firstTime:
        find_common = {'type': 'common_prompt'}
        find_common_result = myCommonList.find_one(find_common)
        response = choice(find_common_result['content'])
        # 記錄對話過程
        createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
        dialog_id += 1
    else:
        response = ''
        dialog_id = dialog_id

    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }
    }}

    second_login = False
    print(response)
    return response_dict


# 比對故事內容
def evaluate(req, predictor):
    print("EVALUATE")
    global now_user_say, repeat_content, record_list, match_verb, match_entity, firstTime, now_index, dialog_id, qa_id, double_check, state
    firstTime = False
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
        no_match = False
        now_index = []
        repeat_content = []
        response = ''
        response_dict = {}
        stop_words = list(stopwords.words('english'))
        for i in ["yourself", "there", "once", "having", "they", "its", "yours", "itself", "is", "him", "themselves", "are",
                  "we", "these", "your", "his", "me", "were", "her", "himself", "this", "our", "their", "ours", "had",
                  "she", "all", "no", "them", "same", "been", "have", "yourselves", "he", "you", "herself", "has", "myself",
                  "those", "i", "being", "theirs", "my", "against", "it", "she's", 'hers']:
            stop_words.remove(i)
        for i in range(len(stop_words)):
            stop_words[i] = " "+stop_words[i]+" "
        stop_words.extend([' . ', ' , ', '"', ' ! '])
        connect()

        # 記錄對話過程
        dialog_id = dialog_id
        createLibrary.addDialog(bookName, session_id, dialog_id, 'Student ' + user_id, userSay, time)
        dialog_id += 1

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
                print('第' + str(cursor['Sentence_id']) + '句相似度：' + str(cosine.similarity_profiles(p1, p2)))
                value = cosine.similarity_profiles(p1, p2)
                if value >= 0.5:
                    similarity_sentence[cursor['Sentence_id']] = value
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
                    if (result['pos'][j] == 'VERB' and result['predicted_dependencies'][j] != 'aux') or (result['pos'][j] == 'AUX' and result['predicted_dependencies'][j] == 'root'):
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

                        story_c1 = myVerbList.find_one({"Sentence_id": similarity_index[0]})['C1']
                        story_v = myVerbList.find_one({"Sentence_id": similarity_index[0]})['Verb']
                        story_c2 = myVerbList.find_one({"Sentence_id": similarity_index[0]})['C2']

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
                                    for i in wn._morphy(word, pos='v'):
                                        word_morphy.append(i)
                                for index in word_morphy:
                                    #找同義字
                                    while True:
                                        try:
                                            trans_word_pre = translator.translate(index, src='en', dest="zh-TW").text
                                            trans_word = translator.translate(trans_word_pre, dest="en").extra_data['parsed']
                                            if len(trans_word) > 3:
                                                for i in trans_word[3][5][0]:
                                                    if i[0] == 'verb':
                                                        for index in i[1]:
                                                            word_case.append(index[0])
                                                        break
                                            break
                                        except Exception as translator_error:
                                            print(translator_error)
                                word_case.extend(word_morphy)
                                print(word_case)
                                for index in word_case:
                                    for v_index in story_v:
                                        verb_allResult = wn._morphy(v_index, pos='v')
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
                                            trans_word = translator.translate(trans_word_pre, dest="en").extra_data['parsed']
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
                                    {"Sentence_id": similarity_index[0], "Student_elaboration": {'$exists': True}})
                                if exist_elaboration is not None:
                                    # 若有學生曾輸入過的詮釋 > 回答該句
                                    repeat_content.append(all_cursor[similarity_index[0]]['Student_elaboration'])
                                else:
                                    result = all_cursor[similarity_index[0]]['Sentence_translate']
                                    for word in ['。', '，', '！']:
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
                                    }
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
                    }
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
                                qa_id = cursor['QA_id']
                                QAMatch = True
                                response_dict = {
                                    "scene": {
                                        "next": {
                                            'name': 'INQUIRE'
                                        }
                                    }
                                }
                                break
                    if all_QA_cursor is None or not QAMatch:
                        if all_QA_cursor is None:
                            qa_id = 1
                        else:
                            qa_id = all_QA_cursor.count() + 1

                        # 存入比對不到的使用者對話similarity_sentence
                        createLibrary.addQuestion(bookName, qa_id, dialog_id - 1, userSay)

                        # 請使用者補充說明
                        find_common = {'type': 'common_match_F'}
                        find_common_result = myCommonList.find_one(find_common)
                        response = choice(find_common_result['content'])

                        double_check = True

                        # 記錄對話過程
                        createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
                        dialog_id += 1

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

    print(response)
    return response_dict


# 比對正確則覆述使用者說的故事
def repeat(req):
    print("REPEAT")
    global dialog_id, double_check
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    response = ''
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
        find_story_sentence = {'Sentence_id': sentence_id}
        newvalues = {"$set": {'Student_elaboration': now_user_say}}
        myVerbList.update_one(find_story_sentence, newvalues)

    if double_check:
        createLibrary.addElaboration(bookName, qa_id, now_user_say, confidence, sentence_id)

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    dialog_id += 1
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
        }
    }

    print(response)
    return response_dict


# 接續使用者的下一句
def retrive(req):
    print("RETRIVE")
    global now_index, dialog_id, state
    go_expand = False
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    connect()
    all_cursor = myVerbList.find()
    print(record_list)
    if record_list[-1] == 29 or record_list[-1] == 30:
        # 講到最後一句
        go_expand = True
    else:
        if len(now_index) == 0:
            # 沒有新故事
            if len(record_list) == 0:
                # 沒有任何故事就直接講第一句
                find_common = {'type': 'common_return'}
                find_common_result = myCommonList.find_one(find_common)
                result = all_cursor[0]["Sentence_translate"]
                for word in ['。', '，', '！']:
                    result = result.replace(word, ' ')
                response = choice(find_common_result['content']) + ' ' + result
                record_list.append(0)
            else:
                # 依據前次記錄到的句子接續講下一句
                find_condition = {'Sentence_id': record_list[-1]}
                find_result_cursor = myVerbList.find_one(find_condition)
                story_conj = '故事裡還有提到'
                result = find_result_cursor["Sentence_translate"]
                for word in ['。', '，', '！']:
                    result = result.replace(word, ' ')
                response = story_conj + ' ' + result
                if (record_list[-1]) not in record_list:
                    record_list.append(record_list[-1])
        else:
            # 排序now_index
            now_index = sorted(now_index, reverse=True)
            if now_index[0] > all_cursor.count():
                go_expand = True
            else:
                find_condition = {'Sentence_id': now_index[0] + 1}
                find_result_next = myVerbList.find_one(find_condition)
                find_common_follow = {'type': 'common_retrieve'}
                result_follow = myCommonList.find_one(find_common_follow)
                find_common_conj = {'type': 'common_conj'}
                result_conj = myCommonList.find_one(find_common_conj)
                story_conj = choice(result_conj['content'])+choice(result_follow['content'])
                result = find_result_next["Sentence_translate"]
                for word in ['。', '，', '！']:
                    result = result.replace(word, ' ')
                response = story_conj + result
                if (now_index[0] + 1) not in record_list:
                    record_list.append(now_index[0] + 1)

    if go_expand:
        state = True
        find_common = {'type': 'common_expand'}
        find_common_result = myCommonList.find_one(find_common)
        response = "\n"+choice(find_common_result['content'])
        createLibrary.updateUser('Student ' + user_id, bookName, record_list, match_entity, match_verb, state)
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }},
            "scene": {
                "next": {
                    'name': 'Expand'
                }
            }
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
            }
        }

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    dialog_id += 1

    print(response)
    createLibrary.updateUser('Student ' + user_id, bookName, record_list, match_entity, match_verb, state)
    return response_dict


# 確認比對到的QA
def inquire(req):
    print('Inquire')
    global dialog_id, double_check
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']

    find_result = {'QA_id': qa_id}
    result = myElaboration.find_one(find_result)

    # text = '你的意思是指X嗎'
    # response = text.replace('X', result['Elaboration'])

    find_common = {'type': 'common_QA'}
    find_common_result = myCommonList.find_one(find_common)
    find_common_2 = {'type': 'common_repeat'}
    find_common_result_2 = myCommonList.find_one(find_common_2)
    response = choice(find_common_result['content']) + " " + result['Elaboration'] + " " + choice(
        find_common_result_2['content'])
    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    dialog_id += 1

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
    print(response)
    return response_dict


# 二次確認正確 > 覆述 > 接續common_grow_check
# def inquire_double_check(req):
#     print("Inquire_double_check")
#     global dialog_id
#     userSay = req['intent']['query']
#     time = req['user']['lastSeenTime']
#     session_id = req['session']['id']
#
#     if userSay == '對' or userSay == '是' or '恩' in userSay or '嗯' in userSay:
#         find_result = {'QA_id': qa_id}
#         print('QA_id' + str(qa_id))
#         result = myElaboration.find_one(find_result)
#         myquery = {"Confidence": result['Confidence']}
#         newvalues = {"$set": {"Confidence": result['Confidence'] + 1}}
#
#         myElaboration.update_one(myquery, newvalues)
#
#         find_common = {'type': 'common_inqurie_new'}
#         find_common_result = myCommonList.find_one(find_common)
#         find_common_2 = {'type': 'common_repeat'}
#         find_common_result_2 = myCommonList.find_one(find_common_2)
#         response = choice(find_common_result['content']) + ' ' + choice(find_common_result_2['content'])
#
#         # 記錄對話過程
#         createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
#         dialog_id += 1
#
#         response_dict = {"prompt": {
#             "firstSimple": {
#                 "speech": response,
#                 "text": response
#             }},
#             "scene": {
#                 "next": {
#                     'name': 'PROMPT'
#                 }
#             }
#         }
#     else:
#         find_result = {'QA_id': qa_id}
#         result = myElaboration.find_one(find_result)
#         myquery = {"Confidence": result['Confidence']}
#         newvalues = {"$set": {"Confidence": result['Confidence'] - 1}}
#
#         myElaboration.update_one(myquery, newvalues)
#
#         find_common = {'type': 'common_inqurie_new'}
#         find_common_result = myCommonList.find_one(find_common)
#         find_common_2 = {'type': 'common_repeat'}
#         find_common_result_2 = myCommonList.find_one(find_common_2)
#         response = choice(find_common_result['content']) + " " + choice(find_common_result_2['content'])
#
#         response_dict = {"prompt": {
#             "firstSimple": {
#                 "speech": response,
#                 "text": response
#             }},
#             "scene": {
#                 "next": {
#                     'name': 'Prompt'
#                 }
#             }
#         }
#     print(response)
#     return response_dict


# 增加新的Elaboration
def addElaboration(req):
    print('Elaboration')
    global dialog_id, double_check, qa_id
    double_check = False
    userSay = req['intent']['query']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']

    # 暫定信心值
    confidence = 0
    sentence_id = ''
    createLibrary.addElaboration(bookName, qa_id, userSay, confidence, sentence_id)

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'Student ' + user_id, userSay, time)
    dialog_id += 1

    find_common = {'type': 'common_match_T'}
    find_common_result = myCommonList.find_one(find_common)
    find_common_2 = {'type': 'common_repeat'}
    find_common_result_2 = myCommonList.find_one(find_common_2)
    response = choice(find_common_result['content']) + " " + userSay + " " + choice(find_common_result_2['content'])

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    dialog_id += 1

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

    qa_id += 1
    print(response)
    return response_dict


# 學生心得回饋
def expand(req, senta):
    print("Expand")
    global dialog_id, expand_user, suggest_like
    userSay = req['intent']['query']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    response = ''
    if not expand_user:
        find_common = {'type': 'common_like'}
        find_result = myCommonList.find_one(find_common)
        response = choice(find_result['content'])
        expand_user = True
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }}
        }
    else:
        # Senta情感分析
        input_dict = {"text": [userSay]}
        results = senta.sentiment_classify(data=input_dict)
        if results[0]['sentiment_key'] == "positive":
            # 接續詢問使用者喜歡故事的原因
            find_common = {'type': 'common_like_response'}
            find_common2 = {'type': 'common_like_expand'}
            find_result = myCommonList.find_one(find_common)
            find_result2 = myCommonList.find_one(find_common2)
            response = choice(find_result['content'])+' '+choice(find_result2['content'])
            suggest_like = True
            response_dict = {"prompt": {
                "firstSimple": {
                    "speech": response,
                    "text": response
                }},
                "scene": {
                    "next": {
                        'name': 'Feedback'
                    }
                }
            }
        else:
            suggest_like = False
            response_dict = {
                "scene": {
                    "next": {
                        'name': 'Suggest'
                    }
                }
            }
        expand_user = False

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    dialog_id += 1
    print(response)
    return response_dict


def feedback():
    print('Feedback')
    find_common = {'type': 'common_feedback'}
    find_result = myCommonList.find_one(find_common)
    response = choice(find_result['content'])
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }},
        "scene": {
            "next": {
                'name': 'Suggest'
            }
        }
    }
    print(response)
    return response_dict


# 依據學生喜好建議其他書籍
def suggestion(req):
    print("Suggestion")
    global dialog_id, suggest_like
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    if suggest_like:
        find_common = {'type': 'common_like_T'}
        find_result = myCommonList.find_one(find_common)
        bookName_match = bookName.replace('_', ' ')
        book_type = myBookList.find_one({'bookName': bookName_match})['type']
        while bookName_match == bookName.replace('_', ' '):
            bookName_match = myBookList.find_one({'type': book_type})
        response = choice(find_result['content']).replace('OO', book_type).replace('XX', bookName_match['bookName'])
    else:
        find_common_feedback = {'type': 'common_feedback'}
        find_result_feedback = myCommonList.find_one(find_common_feedback)
        find_common = {'type': 'common_like_F'}
        find_result = myCommonList.find_one(find_common)
        book_type = myBookList.find_one({'bookName': bookName.replace('_', ' ')})['type']
        other_book = myBookList.find_one({'type': {'$ne': book_type}})['bookName']
        response = choice(find_result_feedback['content'])+' '+choice(find_result['content']).replace('XX', other_book)

    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }}
    }
    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'chatbot', response, time)
    dialog_id += 1
    print(response)
    return response_dict


def exit(req):
    print("Exit")
    if user_id != '' and bookName != '':
        createLibrary.updateUser('Student ' + user_id, bookName, record_list, match_entity, match_verb, state)


if __name__ == '__main__':
    print(0)

