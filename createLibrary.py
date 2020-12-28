import pymongo
# from google.cloud import translate_v2
from googletrans import Translator
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'dict/key.json'

def connect():
    try:
        # 連接mongo
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")

        myLibrary = myclient.Library
        myBookList = myLibrary.bookList
        myCommonList = myLibrary.commonList

        myBookList.delete_many({})
        myCommonList.delete_many({})

        addBook(myBookList)
        addCommon(myCommonList)

    except Exception as e:
        print(e)


def addBook(myBookList):
    # 新增書單
    bookList = ['Fairy friends']
    translator = Translator()
    # translate_client = translate_v2.Client()
    # source = 'en'
    # target = 'zh-TW'
    for i in range(len(bookList)):
        # while True:
        #     try:
        #         trans_bookName = translate_client.translate(
        #             bookList[i],
        #             source_language=source,
        #             target_language=target)
        #         break
        #     except Exception as e:
        #         print(e)
        book_dict = {'type': '精靈', 'bookName': bookList[i], 'bookNameTranslate': translator.translate(bookList[i], src="en", dest="zh-TW").text}
        myBookList.insert_one(book_dict)
        print(book_dict)


def addCommon(myCommonList):
    # 新增通用句
    common_start = ['哈囉~你今天看了哪本書呢？', '你想跟我聊哪本書呢？', 'Hi~今天有甚麼有趣的故事書呢？']
    common_start_checkO = ['真巧！我剛好也看過這本書耶！', '我也看過這本書呢！']
    common_start_checkX = ['這本書我還沒看過欸，你想聊聊其他的書嗎？', '我好像沒看過這本書，你還有其他書可以跟我分享嗎？']
    common_prompt = ['可以跟我說說故事裡發生了什麼事嗎？', '可以告訴我故事裡的角色發生了甚麼事嗎？']
    common_evaluate = ['哦~原來如此', '你講得很好呢！', '你說的對~']
    common_follow = ['所以故事裡', '故事裡提到', '所以故事中發生了']
    common_conj = ['然後', '接下來', '而且']
    common_repeat = ['那接下來又發生了甚麼事呢？']
    # 比對不到 進入Inqurie
    common_prompt_checkO = ['別的小朋友也講過類似的事情，他告訴我', '我有聽過類似的故事', '哦~原來如此']
    common_prompt_checkX = ['我不知道這件事耶，可以告訴我發生了甚麼事嗎？', '我好像沒看到這部分耶，你可以說說看你的想法嗎？', '我不知道有這個事情耶？你可以告訴我嗎',
                            '你說的事我沒聽過欸, 你可以更詳細一點告訴我嗎？']
    common_prompt_return = ['前面的故事還有提到', '前面我還知道', '故事前面還有']
    common_inqurie_new = ['哦哦哦我知道了~', '原來如此~我了解了']
    common_grow_check = ['你的意思是指X嗎', '你是要說X嗎', '你是在說X嗎']
    common_prompt_duplicate = ['你剛剛說過一樣的故事了唷']
    common_expand_student = ['你喜歡這本書嗎？', '你喜歡書裡的哪個部份呢？', '你覺得這本書怎麼樣？']
    common_expand_chatbot = ['我對這本書的感想是', '讀過這本書的小朋友的感想是']
    common_expand_chatbot_O = ['那我推薦你這本書，他也是屬於XX類型的書！', '讓我也推薦給你一本XX的書！']
    common_expand_chatbot_X = ['那我推薦你這本書']
    common = [common_start, common_start_checkO, common_start_checkX, common_prompt, common_evaluate, common_follow,
              common_conj, common_repeat, common_prompt_checkO, common_prompt_checkX, common_prompt_return,
              common_inqurie_new, common_grow_check,
              common_prompt_duplicate, common_expand_student, common_expand_chatbot, common_expand_chatbot_O,
              common_expand_chatbot_X]
    common_type = ["common_start", "common_start_checkO", "common_start_checkX", "common_prompt", "common_evaluate",
                   "common_follow", "common_conj", "common_repeat", "common_prompt_checkO", "common_prompt_checkX",
                   "common_prompt_return", "common_inqurie_new", "common_grow_check", "common_prompt_duplicate",
                   "common_expand_student",
                   "common_expand_chatbot", "common_expand_chatbot_O", "common_expand_chatbot_X"]

    for i in range(len(common)):
        common_dict = {'type': common_type[i], 'content': common[i]}
        myCommonList.insert_one(common_dict)
        print(common_dict)


def addUserDB(user_id, nowBook_name, messaging, bot_say, record_index_list, keyword, match):
    # 連接mongo
    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myBook = myClient[nowBook_name]
    myUserList = myBook.UserTable
    # (使用者 書名 機器人說話內容 學生說話內容
    user_dict = {'user_id': user_id, 'user_say': messaging, 'bot_say': bot_say, 'userRecord': sorted(record_index_list),
                 'keyword': keyword, 'match': match}
    myUserList.insert_one(user_dict)


def addState(sender_id, nowBook_name, state, feedback, record_index_list):
    # 連接mongo
    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myLibrary = myClient.Library
    myStateList = myLibrary.StateTable

    # (使用者帳號 書名 總句數 學生完成的句子 學生感想
    if state == 'Finish':
        user_dict = {'sender_id': sender_id, 'title': nowBook_name, 'state': state,
                     'userRecord': sorted(record_index_list), 'feedback': feedback}
    else:
        if len(record_index_list) != 0:
            user_dict = {'sender_id': sender_id, 'title': nowBook_name, 'state': state,
                         'userRecord': sorted(record_index_list)}
        else:
            user_dict = {'sender_id': sender_id, 'title': nowBook_name, 'state': state}

    myStateList.insert_one(user_dict)


# 新增故事書SVO data
def addBookInfo(bookName, c1, verb, c2, sentence, sentence_Translate, sentenceID, speaker, speak_to, contain_keyword):
    # 連接mongo
    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    myVerbList = myBook.VerbTable

    mydict = {'Sentence_id': sentenceID, 'C1': c1, 'Verb': verb, 'C2': c2, 'Sentence': sentence, 'sentence_Translate': sentence_Translate, 'Speaker': speaker, 'Speak_to': speak_to, 'Contain_keyword': contain_keyword}
    myVerbList.insert(mydict)
    print(mydict)


def addBookKeyword(bookName, entityList, verbList):
    # 連接mongo
    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    myKeyList = myBook.KeywordTable

    mydict = {'Entity_List': entityList, 'Verb_List': verbList}
    myKeyList.insert(mydict)
    print(mydict)


def addUser(userId, bookName, record_list, match_entity, match_verb, state):
    # 連接mongo
    book_exist = False

    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myLibrary = myClient.Library
    myUserList = myLibrary.userTable
    bookTalkSummary = {bookName: {'Sentence_id_list': record_list, 'Entity_list': match_entity,
                                              'Verb_list': match_verb, 'Finish': state}}

    mydict = {'User_id': userId, 'BookTalkSummary': bookTalkSummary}
    myUserList.insert(mydict)
    print(mydict)
    # if myUserList.find() is None:
    #     #資料庫無資料
    #     find_condition = {'User_id': userId}
    #     now_user = myUserList.find_one(find_condition)
    #     # 若沒有該使用者之資料
    #     if now_user is None:
    #         # 直接新增一筆
    #         mydict = {'User_id': userId, 'BookTalkSummary': bookTalkSummary}
    #         myUserList.insert(mydict)
    #         print(mydict)
    #     # 有該使用者資料
    #     else:
    #         # 有該本書之資料
    #         list_item = list(now_user['BookTalkSummary'].keys())
    #         for i in list_item:
    #             if i == bookName:
    #                 # newvalues = {"$set": bookTalkSummary}
    #                 # myUserList.update_one(find_condition, newvalues)
    #                 book_exist = True
    #                 break
    #         if not book_exist:
    #             print()
    #             # 同一筆資料新增東西
    #             newvalues = {"$set": now_user['BookTalkSummary'].append(bookTalkSummary)}
    #             myUserList.update_one(find_condition, newvalues)


def addDialog(bookName, session_id, dialog_id, speaker_id, content, time):
    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    allDialog = myBook.S_R_Dialog

    mydict = {'Session_id': session_id, 'Dialog_id': dialog_id, 'Speaker_id': speaker_id, 'Content': content, 'Time': time}
    allDialog.insert(mydict)
    print(mydict)


def addQuestion(bookName, qa_id, dialog_id, response):
    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    QATable = myBook.QATable

    mydict = {'QA_id': qa_id, 'Dialog_id': dialog_id, 'Response': response}
    QATable.insert(mydict)
    print(mydict)


def addElaboration(bookName, qa_id, elaboration, confidence, sentence_id):
    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    Elaboration_Table = myBook.Elaboration

    mydict = {'QA_id': qa_id, 'Elaboration': elaboration, 'Confidence': confidence, 'Sentence_id': sentence_id}
    Elaboration_Table.insert(mydict)
    print(mydict)


if __name__ == "__main__":
    connect()
