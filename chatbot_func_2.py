from random import choice
from nltk.corpus import stopwords
from strsimpy.cosine import Cosine
from googletrans import Translator
from nltk.corpus import wordnet
import pymongo
import connectDB
import random

myClient: object
myBotData: object
myBookList: object
myCommonList: object
myUserList: object


def check_input(req):
    print('確認說話內容')
    response = ''
    userSay = req['intent']['query']
    if userSay == '我說完了':
        bookName = req['session']['params']['User_book']
        time = req['user']['lastSeenTime']
        user_id = req['session']['params']['User_id']
        session_id = req['session']['id']
        dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
        nowBook = myClient[dbBookName]
        myMaterialList = nowBook['MaterialTable']
        myDialogList = nowBook['S_R_Dialog']
        dialog_index = myDialogList.find().count()
        dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
        material_result = myMaterialList.find_one({})
        # 判斷接下來要進哪個引導問題
        nowScene = req['session']['params']['NowScene']
        connectDB.addDialog(myDialogList, dialog_id, 'Student ' + user_id, userSay, time, session_id, nowScene)
        if nowScene == 'Prompt_character':
            response_dict = {"scene": {
                "next": {
                    'name': 'Prompt_action'
                }
            }}
        elif nowScene == 'Prompt_action' and 'Sentence_id' in material_result:
            response_dict = {"scene": {
                "next": {
                    'name': 'Prompt_dialog'
                }
            }}
        else:
            response_dict = {"scene": {
                "next": {
                    'name': 'Expand'
                }
            }}
    else:
        scene = req['session']['params']['NextScene']
        response_dict = {"scene": {
            "next": {
                'name': scene
            }
        }, "session": {
            "params": {
                'User_say': userSay
            }}
        }

    print(response)
    return response_dict


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


# 詢問班級
def user_login():
    print("START_class")
    response = '哈囉！請先告訴我你的班級唷！'
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        },
        'suggestions': [{'title': '丁班'},
                        {'title': '戊班'}]
    }}
    # response = '魚姐姐現在正在休息唷！'
    # response_dict = {"prompt": {
    #     "firstSimple": {
    #         "speech": response,
    #         "text": response
    #     }},
    #     "scene": {
    #         "next": {
    #             'name': 'actions.scene.END_CONVERSATION'
    #         }
    #     }
    # }
    return response_dict


# 詢問座號
def input_userId(req):
    print("START_id")
    userInput = req['intent']['query']
    if userInput != '丁班' and userInput != '戊班':
        response = '要先點選班級對應的選項告訴我唷，'
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }
        }, "scene": {
            "next": {
                'name': 'User_login'
            }}}
    else:
        response = '好唷！那你的座號是多少呢！'
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }
        }, "scene": {
            "next": {
                'name': 'Check_input'
            }}, "session": {
            "params": {
                'NextScene': 'Get_bookName'
            }
        }}
    return response_dict


# 詢問書名
def start_chat(req):
    print("START_ask")
    if 'User_second_check' in req['session']['params'].keys():
        second_check = req['session']['params']['User_second_check']
    else:
        second_check = False
    if second_check:
        response = ''
        user_id = req['session']['params']['User_id']
    else:
        userClass = req['session']['params']['User_class']
        if userClass == 'DingBan':
            userClass = '丁班'
        user_id = userClass + req['session']['params']['User_say'].replace('號', '')
        print('使用者：' + str(user_id))
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
                allBook.reverse()
                for i in range(len(allBook[0:2])):
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
        }}, "session": {
        "params": {
            'User_id': user_id,
            'NextScene': 'Match_book'
        }
    }, "scene": {
        "next": {
            'name': 'Check_input'
        }}
    }
    print(response)
    return response_dict


# 根據相似度比對結果顯示書名選項給使用者直接點選
def match_book(req):
    print('比對書名')
    userSay = req['session']['params']['User_say']
    session_id = req['session']['id']
    connect()
    if 'User_first_match' in req['session']['params'].keys():
        first_match = req['session']['params']['User_first_match']
    else:
        first_match = True
    # 抓出所有書名
    bookDB = []
    for i in myBookList.find():
        bookDB.append(i['bookName'])
        bookDB.append(i['bookNameTranslated'])
    if first_match:
        # 第一次先找出相似書名給使用者確認
        similarity_book = []
        for index in range(len(bookDB)):
            cosine = Cosine(2)
            s1 = userSay.lower()
            s2 = bookDB[index].lower()
            p1 = cosine.get_profile(s1)
            p2 = cosine.get_profile(s2)
            if p1 == {}:
                # 避免輸入字串太短
                break
            else:
                print(s2 + '，相似度：' + str(cosine.similarity_profiles(p1, p2)))
                value = cosine.similarity_profiles(p1, p2)
                if value >= 0.45:
                    if index == 0:
                        similarity_book.append(bookDB[index])
                    else:
                        if index % 2 == 0:
                            similarity_book.append(bookDB[index])
                        else:
                            similarity_book.append(bookDB[index - 1])
        print(similarity_book)
        similarity_book = list(set(similarity_book))
        if len(similarity_book) == 0:
            second_check = True
            first_match = True
            # 無相似書籍 重新輸入
            find_common = {'type': 'common_book_F'}
            find_common_result = myCommonList.find_one(find_common)
            response = choice(find_common_result['content'])
            response_dict = {"prompt": {
                "firstSimple": {
                    "speech": response,
                    "text": response
                }},
                "session": {
                    "params": {
                        'User_first_match': first_match,
                        'User_second_check': second_check
                    }
                }, "scene": {
                    "next": {
                        'name': 'Get_bookName'
                    }}
            }
        else:
            first_match = False
            button_item = []
            temp_bookList = {}
            allBook = ''
            for index in range(len(similarity_book)):
                temp_bookList[str(index + 1)] = similarity_book[index]
                button_item.append({'title': str(index + 1)})
                if index == 0:
                    allBook += str(index + 1) + '：' + similarity_book[index]
                else:
                    allBook += "、" + str(index + 1) + '：' + similarity_book[index]
            button_item.append({'title': '都不是'})
            response = '我有看過 ' + allBook + " 你是在指哪一本呢? 告訴我書名對應的號碼吧"
            response_dict = {"prompt": {
                "firstSimple": {
                    "speech": response,
                    "text": response
                },
                'suggestions': button_item
            }, "session": {
                "params": {
                    'User_first_match': first_match,
                    'User_temp_bookList': temp_bookList
                }
            }}
    else:
        userInput = req['intent']['query']
        temp_bookList = req['session']['params']['User_temp_bookList']
        if userInput in temp_bookList.keys():
            time = req['user']['lastSeenTime']
            user_id = req['session']['params']['User_id']
            bookName = temp_bookList[userInput]
            dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
            nowBook = myClient[dbBookName]
            myDialogList = nowBook['S_R_Dialog']
            book_finish = False

            dialog_index = myDialogList.find().count()
            if dialog_index == 0:
                dialog_id = 0
            else:
                dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
            find_common = {'type': 'common_book_T'}
            find_common_result = myCommonList.find_one(find_common)
            response = choice(find_common_result['content'])

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
                        book_finish = True

            # 記錄對話過程
            connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id, req['scene']['name'])

            if book_finish:
                first_match = True
                second_check = True
                response_dict = {"prompt": {
                    "firstSimple": {
                        "speech": response,
                        "text": response
                    }},
                    "scene": {
                        "next": {
                            'name': 'Get_bookName'
                        }
                    },
                    "session": {
                        "params": {
                            'User_first_match': first_match,
                            'User_second_check': second_check
                        }
                    }
                }
            else:
                state = False
                # 建立使用者資料
                connectDB.updateUser(myUserList, user_id, bookName, state)
                response_dict = {"prompt": {
                    "firstSimple": {
                        "speech": response,
                        "text": response
                    }},
                    "scene": {
                        "next": {
                            'name': 'Prompt_character'
                        }
                    },
                    "session": {
                        "params": {
                            'User_book': bookName
                        }
                    }
                }
        else:
            first_match = True
            second_check = True
            # 重新輸入
            response = '再跟我說一次書名吧！'
            response_dict = {"prompt": {
                "firstSimple": {
                    "speech": response,
                    "text": response
                }},
                "session": {
                    "params": {
                        'User_first_match': first_match,
                        'User_second_check': second_check
                    }
                }, "scene": {
                    "next": {
                        'name': 'Get_bookName'
                    }}
            }

    return response_dict


def Prompt_character(req):
    response = '我知道這個故事的角色有：XX，'
    session_id = req['session']['id']
    time = req['user']['lastSeenTime']
    bookName = req['session']['params']['User_book']
    dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
    nowBook = myClient[dbBookName]
    myMaterialList = nowBook['MaterialTable']
    # 搜尋書本素材
    find_material_result = myMaterialList.find_one({})
    # 列出書本角色
    response_tmp = ''
    for character in find_material_result['Character']:
        if response_tmp != '':
            response_tmp += '，還有，'
        response_tmp += character
    response = response.replace('XX', response_tmp)

    # 如果角色陣列長度為1：修改字串
    response_tmp = '你知道他們有發生哪些事嗎？'
    if len(find_material_result['Character']) == 1:
        response_tmp = '你知道他有發生哪些事嗎？'
    response += response_tmp

    # 記錄對話
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id, req['scene']['name'])

    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }
    }, "session": {
        "params": {
            'NowScene': 'Prompt_character',
            'NextScene': 'Prompt_response'
        }
    }, "scene": {
        "next": {
            'name': 'Check_input'
        }}
    }
    print(response)
    return response_dict


def Prompt_action(req):
    response = '在故事中我有看到：XX，'
    session_id = req['session']['id']
    time = req['user']['lastSeenTime']
    bookName = req['session']['params']['User_book']
    dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
    nowBook = myClient[dbBookName]
    myVerbList = nowBook['VerbTable']
    myMaterialList = nowBook['MaterialTable']
    # 搜尋書本素材
    find_material_result = myMaterialList.find_one({})
    # 列出書本動作
    response_tmp = ''
    for verb in find_material_result['Main_Verb']:
        result = random.choice(list(myVerbList.find({'Verb': verb})))
        if response_tmp != '':
            response_tmp += '，還有，'
        response_tmp += result['Sentence_translate']
    response = response.replace('XX', response_tmp)

    response_tmp = '你知道還有發生哪些事嗎？'
    response += response_tmp

    # 記錄對話
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id, req['scene']['name'])

    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }
    }, "session": {
        "params": {
            'NowScene': 'Prompt_action',
            'NextScene': 'Prompt_response'
        }
    }, "scene": {
        "next": {
            'name': 'Check_input'
        }}
    }
    print(response)
    return response_dict


def Prompt_dialog(req):
    print('對話引導')
    session_id = req['session']['id']
    time = req['user']['lastSeenTime']
    bookName = req['session']['params']['User_book']
    dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
    nowBook = myClient[dbBookName]
    myVerbList = nowBook['VerbTable']
    myMaterialList = nowBook['MaterialTable']
    # 搜尋書本素材
    find_material_result = myMaterialList.find_one({})
    # 找出隨機一段對話
    find_common = {'type': 'common_Prompt_dialog'}
    find_common_result = myCommonList.find_one(find_common)
    response = choice(find_common_result['content'])
    dialog_sentenceID = choice(find_material_result['Sentence_id'])
    result = myVerbList.find_one({'Sentence_Id': dialog_sentenceID})['Sentence_translate'] + 'X' + myVerbList.find_one({'Sentence_Id': dialog_sentenceID + 1})['Sentence_translate']
    for word in ['。', '，', '！', '：']:
        result = result.replace(word, ' ')
    dialog = result.replace('X', '，然後 ')
    find_common = {'type': 'common_dialog_repeat'}
    find_common_repeat = myCommonList.find_one(find_common)
    response += dialog + choice(find_common_repeat['content'])
    # 記錄對話
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id, req['scene']['name'])

    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }
    }, "session": {
        "params": {
            'NowScene': 'Prompt_dialog',
            'NextScene': 'Prompt_response'
        }
    }, "scene": {
        "next": {
            'name': 'Check_input'
        }}
    }
    print(response)
    return response_dict


def Prompt_response(req, predictor):
    print('系統回覆')
    userSay = req['session']['params']['User_say']
    user_id = req['session']['params']['User_id']
    userClass = req['session']['params']['User_class']
    session_id = req['session']['id']
    time = req['user']['lastSeenTime']
    bookName = req['session']['params']['User_book']
    dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
    nowBook = myClient[dbBookName]
    myDialogList = nowBook['S_R_Dialog']
    myVerbList = nowBook['VerbTable']

    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    connectDB.addDialog(myDialogList, dialog_id, 'Student ' + user_id, userSay, time, session_id,
                        req['session']['params']['NowScene'])

    # 比對故事
    matchStory_all = False
    match_response = ''
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
    translator = Translator()
    # 將原句翻譯
    while True:
        try:
            trans_word = translator.translate(userSay, src='zh-TW', dest="en").text
            break
        except Exception as e:
            print(e)
    similarity_sentence = {}
    post_similarity = ''
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
        if p1 == {}:
            # 避免輸入字串太短
            break
        else:
            print('第' + str(cursor['Sentence_Id']) + '句相似度：' + str(cosine.similarity_profiles(p1, p2)))
            value = cosine.similarity_profiles(p1, p2)
            if value >= 0.5:
                similarity_sentence[cursor['Sentence_Id']] = value
    similarity_sentence = sorted(similarity_sentence.items(), key=lambda x: x[1], reverse=True)
    print('similarity_sentence：' + str(similarity_sentence))
    twoColumn = []
    if list(similarity_sentence):
        # 有相似的句子
        result = predictor.predict(
            sentence=trans_word
        )
        user_c1 = []
        user_v = []
        user_c2 = []
        v = False
        userColumn_count = 0
        for j in range(len(result['pos'])):
            if v == False and (
                    result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN' or result['pos'][j] == 'PRON'):
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
        if list(user_c1):
            userColumn_count += 1
        if list(user_v):
            userColumn_count += 1
        if list(user_c2):
            userColumn_count += 1

        print('USER輸入中的S:' + str(user_c1) + ',V:' + str(user_v) + ',O:' + str(user_c2) + '欄位數量：' + str(
            userColumn_count))

        # 使用者輸入結構超過兩欄位才判斷
        if userColumn_count >= 2:
            for similarity_index in similarity_sentence:
                print(similarity_index[0])

                matchColumn_count = 0
                checkC1 = False
                checkC2 = False
                checkVerb = False

                storyMatch_count = 0
                story_c1 = myVerbList.find_one(
                    {'Sentence_Id': similarity_index[0], "C1": {'$exists': True}})
                if story_c1 is not None:
                    story_c1 = myVerbList.find_one({'Sentence_Id': similarity_index[0]})['C1']
                    storyMatch_count += 1
                story_v = myVerbList.find_one(
                    {'Sentence_Id': similarity_index[0], "Verb": {'$exists': True}})
                if story_v is not None:
                    story_v = myVerbList.find_one({'Sentence_Id': similarity_index[0]})['Verb']
                    storyMatch_count += 1
                story_c2 = myVerbList.find_one(
                    {'Sentence_Id': similarity_index[0], "C2": {'$exists': True}})
                if story_c2 is not None:
                    story_c2 = myVerbList.find_one({'Sentence_Id': similarity_index[0]})['C2']
                    storyMatch_count += 1
                # 滿足兩個欄位
                if storyMatch_count > 1:
                    # 先比對C1
                    word_case = []
                    if not checkC1 and story_c1 is not None:
                        for word in user_c1:
                            word_case = [word, word.lower(), word.capitalize()]
                        word_case = list(set(word_case))
                        # word是否在storyC1中
                        for index in word_case:
                            for c1_index in story_c1:
                                if c1_index == index:
                                    print(c1_index)
                                    checkC1 = True
                                    matchColumn_count += 1
                                    break
                            if checkC1:
                                break
                    # 找V
                    if not checkVerb and story_v is not None:
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
                                        matchColumn_count += 1
                                        break
                                if checkVerb:
                                    break
                            if checkVerb:
                                break
                    # 找C2
                    if not checkC2 and story_c2 is not None:
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
                                    matchColumn_count += 1
                                    break
                            if checkC2:
                                break

                    if matchColumn_count == 2:
                        if similarity_index[0] not in twoColumn:
                            twoColumn.append(similarity_index[0])
                    print(str(checkC1) + ',' + str(checkC2) + ',' + str(checkVerb))
                    all_cursor = myVerbList.find()
                    if matchColumn_count == 3:
                        # 比對成功
                        matchStory_all = True
                        find_common = {'type': 'common_match_T'}
                        find_common_result = myCommonList.find_one(find_common)

                        exist_elaboration = myVerbList.find_one(
                            {"Sentence_Id": similarity_index[0], "Student_elaboration": {'$exists': True}})
                        if exist_elaboration is not None:
                            # 若有學生曾輸入過的詮釋 > 回答該句
                            match_response = choice(find_common_result['content']) + ' 還有小朋友跟我分享過 ' + choice(
                                all_cursor[similarity_index[0]]['Student_elaboration'])
                        else:
                            result = all_cursor[similarity_index[0]]['Sentence_translate']
                            for word in ['。', '，', '！', '“', '”', '：']:
                                result = result.replace(word, ' ')
                            match_response = choice(find_common_result['content']) + result
                        break
                    else:
                        similarity_sentence.remove(similarity_index)

    if matchStory_all:
        if userClass == '戊班':
            # 獎勵機制
            user_result = myUserList.find_one({'User_id':user_id})
            user_result_updated = connectDB.copy.deepcopy(user_result)
            if 'Score' not in user_result_updated['BookTalkSummary'][bookName]:
                user_result_updated['BookTalkSummary'][bookName].update({'Score': 0})
            user_result_updated['BookTalkSummary'][bookName]['Score'] += 3
            myUserList.update_one(user_result, {'$set':user_result_updated})

            common_result = myCommonList.find_one({'type':'common_score'})
            response_star = choice(common_result['content'])
            response_star = response_star.replace('X', str(user_result_updated['BookTalkSummary'][bookName]['Score']))
            response_star_copy = response_star
            response_star += '⭐' * user_result_updated['BookTalkSummary'][bookName]['Score']

            response = match_response +response_star+ '那接下來還有嗎？'
            response_speech = match_response +response_star_copy+ '那接下來還有嗎？'
        else:
            response = match_response + '那接下來還有嗎？'
            response_speech = match_response + '那接下來還有嗎？'
    else:
        if len(twoColumn) != 0:
            print('有兩欄位的')
            twoColumnMatch = choice(twoColumn)
            print(twoColumnMatch)
            # 比對成功
            find_common = {'type': 'common_match_T'}
            find_common_result = myCommonList.find_one(find_common)
            exist_elaboration = myVerbList.find_one(
                {"Sentence_Id": twoColumnMatch, "Student_elaboration": {'$exists': True}})
            if exist_elaboration is not None:
                # 若有學生曾輸入過的詮釋 > 回答該句
                response = choice(find_common_result['content']) + ' 還有小朋友跟我分享過 ' + choice(
                    all_cursor[twoColumnMatch]['Student_elaboration'])
            else:
                result = all_cursor[twoColumnMatch]['Sentence_translate']
                for word in ['。', '，', '！', '“', '”', '：']:
                    result = result.replace(word, ' ')
                response = choice(find_common_result['content']) + result

            if userClass == '戊班':
                # 獎勵機制
                user_result = myUserList.find_one({'User_id': user_id})
                user_result_updated = connectDB.copy.deepcopy(user_result)
                if 'Score' not in user_result_updated['BookTalkSummary'][bookName]:
                    user_result_updated['BookTalkSummary'][bookName].update({'Score': 0})
                user_result_updated['BookTalkSummary'][bookName]['Score'] += 3
                myUserList.update_one(user_result, {'$set': user_result_updated})

                common_result = myCommonList.find_one({'type': 'common_score'})
                response_star = choice(common_result['content'])
                response_star = response_star.replace('X', str(user_result_updated['BookTalkSummary'][bookName]['Score']))
                response_star_copy = response_star
                response_star += '⭐' * user_result_updated['BookTalkSummary'][bookName]['Score']

                response += response_star + '那接下來還有嗎？'
                response_speech = response + response_star_copy + '那接下來還有嗎？'
            else:
                response += '那接下來還有嗎？'
                response_speech = response
        else:
            # 沒比對到的固定回覆
            find_common = {'type': 'common_Prompt_response'}
            find_common_result = myCommonList.find_one(find_common)
            response = choice(find_common_result['content'])
            response_speech = response


    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id,
                        req['session']['params']['NowScene'])
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response_speech,
            "text": response
        }
    }, "scene": {
        "next": {
            'name': 'Check_input'
        }}
    }
    print(response)
    return response_dict


# 學生心得回饋
def expand(req):
    print("Expand")
    state = True
    user_id = req['session']['params']['User_id']
    bookName = req['session']['params']['User_book']
    time = req['user']['lastSeenTime']
    session_id = req['session']['id']
    dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
    nowBook = myClient[dbBookName]
    myDialogList = nowBook['S_R_Dialog']
    if 'User_expand' in req['session']['params'].keys():
        expand_user = req['session']['params']['User_expand']
    else:
        expand_user = False
    if not expand_user:
        find_common_expand = {'type': 'common_expand'}
        common_result_expand = myCommonList.find_one(find_common_expand)
        find_common = {'type': 'common_like'}
        find_result = myCommonList.find_one(find_common)
        response = choice(common_result_expand['content']) + ' ' + choice(find_result['content'])
        expand_user = True
        # 記錄對話過程
        dialog_index = myDialogList.find().count()
        dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
        connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id, req['scene']['name'])
        response_dict = {"prompt": {
            "firstSimple": {
                "speech": response,
                "text": response
            }, 'suggestions': [{'title': '喜歡'},
                               {'title': '還好'},
                               {'title': '不喜歡'}]},
            'session': {
                'params': {
                    'User_expand': expand_user
                }
            }
        }
    else:
        response = ''
        suggest_like = False
        dialog_index = myDialogList.find().count()
        dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
        userSay = req['intent']['query']
        connectDB.addDialog(myDialogList, dialog_id, 'Student ' + user_id, userSay, time, session_id,
                            req['scene']['name'])
        if userSay == '還好' or userSay == '普通':
            response = '這樣啊！那是為甚麼呢？'
            suggest_like = False
        elif userSay == '喜歡':
            # 接續詢問使用者喜歡故事的原因
            find_common = {'type': 'common_like_response'}
            find_common2 = {'type': 'common_like_expand'}
            find_result = myCommonList.find_one(find_common)
            find_result2 = myCommonList.find_one(find_common2)
            response = choice(find_result['content']) + ' ' + choice(find_result2['content'])
            suggest_like = True
        elif userSay == '不喜歡':
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
                "params": dict(User_sentiment=suggest_like,
                               User_state=state, User_expand=expand_user)}
        }

    connectDB.updateUser(myUserList, user_id, bookName, state)
    print(response)
    return response_dict


# 從資料庫中取資料做為機器人給予學生之回饋
def feedback(req):
    print('Feedback')
    userSay = req['intent']['query']
    user_id = req['session']['params']['User_id']
    bookName = req['session']['params']['User_book']
    session_id = req['session']['id']
    time = req['user']['lastSeenTime']

    dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
    nowBook = myClient[dbBookName]
    myFeedback = nowBook['Feedback']
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    # 記錄對話過程
    connectDB.addDialog(myDialogList, dialog_id, 'Student ' + user_id, userSay, time, session_id, req['scene']['name'])
    find_common = {'type': 'common_feedback'}
    find_result = myCommonList.find_one(find_common)
    find_feedback_student = {'type': 'common_feedback_student'}
    result_feedback_student = myCommonList.find_one(find_feedback_student)
    suggest_like = req['session']['params']['User_sentiment']
    find_like = {'Sentiment': suggest_like}
    result_like = myFeedback.find(find_like)
    if result_like.count() == 0:
        response = '哦！原來是這樣啊！我了解了，'
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
        }
    }
    connectDB.addFeedback(myFeedback, user_id, suggest_like, userSay)
    # 記錄對話過程
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id, req['scene']['name'])
    print(response)
    return response_dict


# 依據學生喜好建議其他書籍
def suggestion(req):
    print("Suggestion")
    connect()
    session_id = req['session']['id']
    suggest_like = req['session']['params']['User_sentiment']
    bookName = req['session']['params']['User_book']
    time = req['user']['lastSeenTime']

    dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
    nowBook = myClient[dbBookName]
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
    story_content = ''
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
    for index in range(len(sort_suggest_book[0:2])):
        if index > 0:
            like_str += choice(result_combine['content']) + sort_suggest_book[index][0]
        else:
            like_str += sort_suggest_book[index][0]
    response = ',' + choice(find_result['content']).replace('XX', like_str) + '\n' + '對這些書有興趣嗎？'
    url = 'http://story.csie.ncu.edu.tw/storytelling/images/chatbot_books/' + sort_suggest_book[0][0] + '.jpg'
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        },
        'suggestions': [{'title': '有興趣'}, {'title': '沒興趣'}],
        'content': {'image': {'url': url, 'alt': sort_suggest_book[0][0], 'height': 1, 'width': 1}}
    },
        "scene": {
            "next": {
                'name': 'Check_input'
            }
        },
        'session': {
            'params':
                {'nowScene': 'Suggest', 'NextScene': 'Interest', 'suggest_book':sort_suggest_book[0:2]}
        }
    }
    # 記錄對話
    connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id, req['scene']['name'])
    print(response)
    return response_dict


def Interest(req):
    userSay = req['intent']['query']
    sort_suggest_book = req['session']['params']['suggest_book']
    if userSay == '有興趣':
        for index in range(len(sort_suggest_book)):
            book_result = myBookList.find_one({'bookName':sort_suggest_book[index][0]})
            book_result_updated = connectDB.copy.deepcopy(book_result)
            if 'Interest' not in book_result_updated:
                book_result_updated.update({'Interest':0})
            book_result_updated['Interest'] += 1
            myBookList.update_one(book_result, {'$set':book_result_updated})
    elif userSay == '沒興趣':
        print()
    response = '謝謝你的分享！期待你下次的故事！Bye Bye！'
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        }},
        "scene": {
            "next": {
                'name': 'actions.scene.END_CONVERSATION'
            }
        }
    }
    return response_dict


def exit_system(req):
    print("Exit")
    if 'User_id' in req['session']['params'].keys() and 'User_book' in req['session']['params'].keys():
        connectDB.updateUser(myUserList, req['session']['params']['User_id'], req['session']['params']['User_book'],
                             req['session']['params']['User_state'])
