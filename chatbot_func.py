from random import choice
from googletrans import Translator
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from strsimpy.cosine import Cosine
import pymongo

import createLibrary

myClient: object
myLibrary: object
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


# 判斷是否為中文
def is_all_chinese(text):
    for _char in text:
        if not '\u4e00' <= _char <= '\u9fa5':
            return False
    return True


def connect():
    global myClient, myLibrary, myBookList, myCommonList, myUserList

    myClient = pymongo.MongoClient("mongodb://localhost:27017/")

    myLibrary = myClient.Library
    myBookList = myLibrary.bookList
    myCommonList = myLibrary.commonList
    myUserList = myLibrary.userTable

    return myBookList, myCommonList, myClient, myUserList


# 詢問座號
def user_login(userSay, session_id, time, predictor):
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
def start_chat(userSay, session_id, time, predictor):
    print("START")
    global user_id
    user_id = userSay
    connect()
    book_record = ''
    find_condition = {'type': 'common_start'}
    find_result = myCommonList.find_one(find_condition)
    response = choice(find_result['content'])
    # 取得該使用者紀錄
    if list(myUserList.find()):
        user_exist = myUserList.find_one({"User_id": 'Student ' + user_id})
        if user_exist is not None:
            find_condition = {'type': 'common_combine'}
            find_result = myCommonList.find_one(find_condition)
            allBook = list(user_exist["BookTalkSummary"].keys())
            for i in range(len(allBook)):
                if i > 0:
                    book_record += choice(find_result['content']) + allBook[i].replace("_", " ")
                else:
                    book_record += allBook[i].replace("_", " ")
            find_condition = {'type': 'common_bookRecord'}
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


# 比對書名
def check_book(userSay, session_id, time, predictor):
    print('CHECK')
    global bookName, myVerbList, allDialog, firstTime, dialog_id, qa_id, myQATable, myElaboration, double_check, second_login, record_list, match_entity, match_verb, state
    connect()

    if is_all_chinese(userSay):
        # 若輸入全中文
        find_condition = {'bookNameTranslate': userSay}
    else:
        find_condition = {'bookName': userSay}
    find_result_cursor = myBookList.find_one(find_condition)

    if find_result_cursor is not None:
        # 比對成功
        firstTime = True
        double_check = False
        dialog_id = 0
        qa_id = 0
        state = False

        bookName = find_result_cursor['bookName'].replace(' ', '_')
        nowBook = myClient[bookName]
        myVerbList = nowBook['VerbTable']
        allDialog = nowBook['S_R_Dialog']
        myQATable = nowBook['QATable']
        myElaboration = nowBook['Elaboration']

        # 取得書本紀錄
        if list(myUserList.find()):
            user_data_load = myUserList.find_one({"User_id": 'Student ' + user_id})
            # 書本狀態紀錄為已完成
            if user_data_load["BookTalkSummary"][bookName]["Finish"]:
                response = '上次我們聊過這本書囉~你有看到新的書可以跟我分享嗎？'
                response_dict = {"prompt": {
                    "firstSimple": {
                        "speech": response,
                        "text": response
                    }}
                }
            else:
                # 抓出過去的故事資料
                record_list = user_data_load["BookTalkSummary"][bookName]["Sentence_id_list"]
                match_entity = user_data_load["BookTalkSummary"][bookName]["Entity_list"]
                match_verb = user_data_load["BookTalkSummary"][bookName]["Verb_list"]

                result = ''
                second_login = True
                if len(record_list) > 1:
                    find_condition = {'type': 'common_combine'}
                    find_result = myCommonList.find_one(find_condition)
                    for i in range(len(record_list)):
                        if i < 3:
                            if i > 0:
                                result += choice(find_result['content']) + myVerbList.find_one({"Sentence_id": int(record_list[-(i+1)])})["sentence_Translate"]
                            else:
                                result += myVerbList.find_one({"Sentence_id": int(record_list[-(i+1)])})["sentence_Translate"]
                else:
                    result = myVerbList.find_one({"Sentence_id": int(record_list[0])})["sentence_Translate"]

                # 新增故事句子 從record裡面挑1句
                for word in ['。', '，', '！']:
                    result = result.replace(word, '')
                find_common = {'type': 'common_book_second'}
                find_common_result = myCommonList.find_one(find_common)
                response = choice(find_common_result['content']) + result

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
        else:
            second_login = False
            find_common = {'type': 'common_start_checkO'}
            find_common_result = myCommonList.find_one(find_common)
            response = choice(find_common_result['content'])

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
    else:
        # 比對失敗
        find_common = {'type': 'common_start_checkX'}
        find_common_result = myCommonList.find_one(find_common)
        response = choice(find_common_result['content'])

        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }
        }}

    print(response)
    return response_dict


# 聊書引導
def prompt(userSay, session_id, time, predictor):
    print("PROMPT")
    global dialog_id, second_login, state
    connect()
    # 曾經有紀錄
    if second_login:
        find_common = {'type': 'common_prompt_secondLogin'}
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
        createLibrary.addUser('Student ' + user_id, bookName, record_list, match_entity, match_verb, state)

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
def evaluate(userSay, session_id, time, predictor):
    print("EVALUATE")
    global now_user_say, repeat_content, record_list, match_verb, match_entity, firstTime, now_index, dialog_id, qa_id, double_check, state
    firstTime = False
    no_match = False
    similarity_search = False
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
            trans_word = trans_word.replace(word, ' ')
        print("USER input:" + str(trans_word))
        # 使用相似度比對
        all_cursor = myVerbList.find()
        for cursor in all_cursor:
            cosine = Cosine(2)
            s1 = trans_word
            s2 = cursor['Sentence']
            for word in stop_words:
                s2 = s2.replace(word, ' ')
            print(s2)
            p1 = cosine.get_profile(s1)
            p2 = cosine.get_profile(s2)
            print('第' + str(cursor['Sentence_id']) + '句相似度：' + str(cosine.similarity_profiles(p1, p2)))
            value = cosine.similarity_profiles(p1, p2)
            if value >= 0.55:
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
                if result['pos'][j] == 'VERB' and result['predicted_dependencies'][j] != 'aux':
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
                similarity_search = True
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
                                # word是否在storyC1中
                                for c1_index in story_c1:
                                    if c1_index == word:
                                        print(word)
                                        checkC1 = True
                                        if word not in match_entity:
                                            match_entity.append(word)
                                        break
                                if checkC1:
                                    break
                            if not checkC1:
                                continue
                        # 找V
                        if not checkVerb:
                            word_case = []
                            for word in user_v:
                                for i in wn._morphy(word, pos='v'):
                                    word_case.append(i)
                                #找同義字
                                while True:
                                    try:
                                        trans_word_pre = translator.translate(word, src='en', dest="zh-TW").text
                                        trans_word = translator.translate(trans_word_pre, dest="en").extra_data['parsed'][1][0][0][5][
                                            0][1]
                                        word_case.extend(trans_word)
                                        break
                                    except Exception as translator_error:
                                        print(translator_error)
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
                            if not checkVerb:
                                continue
                        # 找C2
                        if not checkC2:
                            word_case = []
                            for word in user_c2:
                                word_case.append(word)
                                # 找同義字
                                while True:
                                    try:
                                        trans_word_pre = translator.translate(word, src='en', dest="zh-TW").text
                                        trans_word = translator.translate(trans_word_pre, dest="en").extra_data['parsed'][1][0][0][
                                            5][
                                            0][1]
                                        word_case.extend(trans_word)
                                        break
                                    except Exception as translator_error:
                                        print(translator_error)
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
                            if not checkC2:
                                continue

                        print(str(checkC1) + ',' + str(checkC2) + ',' + str(checkVerb))
                        all_cursor = myVerbList.find()
                        if checkVerb and checkC2 and checkC1:
                            if similarity_index[0] not in record_list:
                                record_list.append(similarity_index[0])
                            now_index.append(similarity_index[0])
                            # 比對成功
                            find_common = {'type': 'common_evaluate'}
                            find_common_result = myCommonList.find_one(find_common)
                            response = choice(find_common_result['content'])

                            exist_elaboration = myVerbList.find_one(
                                {"Sentence_id": similarity_index[0], "Student_elaboration": {'$exists': True}})
                            if exist_elaboration is not None:
                                # 若有學生曾輸入過的詮釋 > 回答該句
                                repeat_content.append(all_cursor[similarity_index[0]]['Student_elaboration'])
                            else:
                                result = all_cursor[similarity_index[0]]['sentence_Translate']
                                for word in ['。', '，', '！']:
                                    result = result.replace(word, ' ')
                                repeat_content.append(result)
                            createLibrary.addUser('Student ' + user_id, bookName, record_list, match_entity, match_verb,
                                                  state)

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
                        similarity_search = True
        else:
            # 沒有相似的句子
            no_match = True

        if similarity_search:
            # 相似度符合 但故事結構不完整 採用最高相似度的句子 接續repeat
            if similarity_sentence[0][0] not in record_list:
                record_list.append(similarity_sentence[0][0])
            now_index.append(similarity_sentence[0][0])

            all_cursor = myVerbList.find()
            find_common = {'type': 'common_evaluate'}
            find_common_result = myCommonList.find_one(find_common)
            response = choice(find_common_result['content'])
            exist_elaboration = myVerbList.find_one(
                {"Sentence_id": similarity_sentence[0][0], "Student_elaboration": {'$exists': True}})
            if exist_elaboration is not None:
                # 若有學生曾輸入過的詮釋 > 回答該句
                repeat_content.append(all_cursor[similarity_sentence[0][0]]['Student_elaboration'])
            else:
                result = all_cursor[similarity_sentence[0][0]]['sentence_Translate']
                for word in ['。', '，', '！']:
                    result = result.replace(word, ' ')
                repeat_content.append(result)
            createLibrary.addUser('Student ' + user_id, bookName, record_list, match_entity, match_verb, state)

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

        elif no_match:
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
                    find_common = {'type': 'common_prompt_checkX'}
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
def repeat(userSay, session_id, time, predictor):
    print("REPEAT")
    global dialog_id, double_check
    # response = ''
    # if len(repeat_content) > 1:
    #     for i in repeat_content:
    #         response += i + " "
    # else:
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
def retrive(userSay, session_id, time, predictor):
    print("RETRIVE")
    global now_index, dialog_id, state
    connect()
    all_cursor = myVerbList.find()
    print(record_list)
    if record_list[-1] == (all_cursor.count() - 1):
        # 講到最後一句
        state = True
        response = "看來你對這本書已經很熟悉了呢!"
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }}
        }
    else:
        if len(now_index) == 0:
            # 沒有新故事
            if len(record_list) == 0:
                # 沒有任何故事就直接講第一句
                find_common = {'type': 'common_prompt_return'}
                find_common_result = myCommonList.find_one(find_common)
                result = all_cursor[0]["sentence_Translate"]
                for word in ['。', '，', '！']:
                    result = result.replace(word, ' ')
                response = choice(find_common_result['content']) + ' ' + result
                record_list.append(0)
            else:
                # 依據前次記錄到的句子接續講下一句
                find_condition = {'Sentence_id': record_list[-1]}
                find_result_cursor = myVerbList.find_one(find_condition)
                story_conj = '故事裡還有提到'
                result = find_result_cursor["sentence_Translate"]
                for word in ['。', '，', '！']:
                    result = result.replace(word, ' ')
                response = story_conj + ' ' + result
                if (record_list[-1]) not in record_list:
                    record_list.append(record_list[-1])
        else:
            # 排序now_index
            now_index = sorted(now_index, reverse=True)
            if now_index[0] > all_cursor.count():
                response = "看來你對這本書已經很熟悉了呢!"
                state = True
            else:
                find_condition = {'Sentence_id': now_index[0] + 1}
                find_result_next = myVerbList.find_one(find_condition)
                find_common = {'type': 'common_conj'}
                find_common_result = myCommonList.find_one(find_common)
                story_conj = choice(find_common_result['content'])
                result = find_result_next["sentence_Translate"]
                for word in ['。', '，', '！']:
                    result = result.replace(word, ' ')
                response = story_conj + result
                if (now_index[0] + 1) not in record_list:
                    record_list.append(now_index[0] + 1)

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
    return response_dict


# 確認比對到的QA
def inquire(userSay, session_id, time, predictor):
    print('Inquire')
    global dialog_id, double_check

    find_result = {'QA_id': qa_id}
    result = myElaboration.find_one(find_result)

    # find_common = {'type': 'common_grow_check'}
    # find_common_result = myCommonList.find_one(find_common)
    # response = choice(find_common_result['content']).replace('X', result['Elaboration'])

    find_common = {'type': 'common_inqurie_new'}
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
def inquire_double_check(userSay, session_id, time, predictor):
    print("Inquire_double_check")
    global dialog_id

    if userSay == '對' or userSay == '是' or '恩' in userSay or '嗯' in userSay:
        find_result = {'QA_id': qa_id}
        print('QA_id' + str(qa_id))
        result = myElaboration.find_one(find_result)
        myquery = {"Confidence": result['Confidence']}
        newvalues = {"$set": {"Confidence": result['Confidence'] + 1}}

        myElaboration.update_one(myquery, newvalues)

        find_common = {'type': 'common_inqurie_new'}
        find_common_result = myCommonList.find_one(find_common)
        find_common_2 = {'type': 'common_repeat'}
        find_common_result_2 = myCommonList.find_one(find_common_2)
        response = choice(find_common_result['content']) + ' ' + choice(find_common_result_2['content'])

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
    else:
        find_result = {'QA_id': qa_id}
        result = myElaboration.find_one(find_result)
        myquery = {"Confidence": result['Confidence']}
        newvalues = {"$set": {"Confidence": result['Confidence'] - 1}}

        myElaboration.update_one(myquery, newvalues)

        find_common = {'type': 'common_inqurie_new'}
        find_common_result = myCommonList.find_one(find_common)
        find_common_2 = {'type': 'common_repeat'}
        find_common_result_2 = myCommonList.find_one(find_common_2)
        response = choice(find_common_result['content']) + " " + choice(find_common_result_2['content'])

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


# 增加新的Elaboration
def addElaboration(userSay, session_id, time, predictor):
    print('Elaboration')
    global dialog_id, double_check, qa_id
    double_check = False

    # 暫定信心值
    confidence = 0
    sentence_id = ''
    createLibrary.addElaboration(bookName, qa_id, userSay, confidence, sentence_id)

    # 記錄對話過程
    createLibrary.addDialog(bookName, session_id, dialog_id, 'Student ' + user_id, userSay, time)
    dialog_id += 1

    find_common = {'type': 'common_inqurie_new'}
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


if __name__ == '__main__':
    list1 = [1, 2, 3, 4, 5]
    a = ''
    for i in range(len(list1)):
        if i < 3:
            a += str(list1[-(i+1)])
    print(a)
