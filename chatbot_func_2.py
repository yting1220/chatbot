from random import choice
from nltk.corpus import stopwords
from strsimpy.cosine import Cosine
import pymongo
import connectDB
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
        elif nowScene == 'Suggest':
            response_dict = {"scene": {
                "next": {
                    'name': 'confirm_interest'
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
    if first_match:
        # 第一次先找出相似書名給使用者確認
        similarity_book = []
        for index in myBookList.find():
            cosine = Cosine(2)
            s1 = userSay.lower()
            if is_all_chinese(userSay):
                # 若輸入全中文
                s2 = index['bookNameTranslated']
            else:
                s2 = index['bookName'].lower()
            p1 = cosine.get_profile(s1)
            p2 = cosine.get_profile(s2)
            if p1 == {}:
                # 避免輸入字串太短
                break
            else:
                print('相似度：' + str(cosine.similarity_profiles(p1, p2)))
                value = cosine.similarity_profiles(p1, p2)
                if value >= 0.45:
                    similarity_book.append(index['bookName'])
        print(similarity_book)
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
    response = '故事中我有看到他們在說話，像是 '
    dialog_sentenceID = choice(find_material_result['Sentence_id'])
    result = myVerbList.find_one({'Sentence_Id': dialog_sentenceID})['Sentence_translate'] + 'X' + myVerbList.find_one({'Sentence_Id': dialog_sentenceID+1})['Sentence_translate']
    for word in ['。', '，', '！', '：']:
        result = result.replace(word, ' ')
    dialog = result.replace('X', '，然後 ')
    response += dialog+'你知道他們還有說了甚麼嗎？'
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


def Prompt_response(req):
    print('系統回覆')
    userSay = req['session']['params']['User_say']
    user_id = req['session']['params']['User_id']
    session_id = req['session']['id']
    time = req['user']['lastSeenTime']
    bookName = req['session']['params']['User_book']
    dbBookName = bookName.replace("'", "").replace('!', '').replace(",", "").replace(' ', '_')
    nowBook = myClient[dbBookName]
    myDialogList = nowBook['S_R_Dialog']
    dialog_index = myDialogList.find().count()
    dialog_id = myDialogList.find()[dialog_index - 1]['Dialog_id'] + 1
    connectDB.addDialog(myDialogList, dialog_id, 'Student ' + user_id, userSay, time, session_id, req['session']['params']['NowScene'])
    response = '你說的很好唷，後面還有嗎？'
    connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id, req['session']['params']['NowScene'])
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
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
        connectDB.addDialog(myDialogList, dialog_id, 'Student ' + user_id, userSay, time, session_id, req['scene']['name'])
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
    # '謝謝你的分享！期待你下次的故事！Bye Bye！'
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
    url = 'http://story.csie.ncu.edu.tw/storytelling/images/chatbot_books/'+bookName+'.jpg'
    response_dict = {"prompt": {
        "firstSimple": {
            "speech": response,
            "text": response
        },
        'suggestions':[{'title':'有興趣'}, {'title':'沒興趣'}],
        'content':{'image': {'url': url, 'alt': bookName, 'height': 1, 'width': 1}}
    },
        "scene": {
            "next": {
                'name': 'Check_input'
            }
        },
        'session':{
            'params':
                {'nowScene':'Suggest', 'nextScene':'confirm_interest'}
        }
    }
    # 記錄對話
    connectDB.addDialog(myDialogList, dialog_id, 'chatbot', response, time, session_id, req['scene']['name'])
    print(response)
    return response_dict


def exit_system(req):
    print("Exit")
    if 'User_id' in req['session']['params'].keys() and 'User_book' in req['session']['params'].keys():
        connectDB.updateUser(myUserList, req['session']['params']['User_id'], req['session']['params']['User_book'], req['session']['params']['User_state'])
