# 建立通用句及書單資料庫
import copy

import pymongo
from googletrans import Translator

myClient: object
myBotData: object
myBookList: object
myCommonList: object


def connect():
    global myClient, myBotData, myBookList, myCommonList
    try:
        # 連接mongo
        myclient = pymongo.MongoClient("mongodb://140.115.53.196:27017/")

        myBotData = myclient.Chatbot
        myBookList = myBotData.bookList
        myCommonList = myBotData.commonList
    except Exception as e:
        print(e)
    return myBookList, myCommonList


def addBook(bookName, bookType):
    connect()
    # 新增書單
    translator = Translator()
    book_dict = {'type': bookType, 'bookName': bookName,
                 'bookNameTranslated': translator.translate(bookName, src="en", dest="zh-TW").text}
    myBookList.insert_one(book_dict)
    print(book_dict)


def addCommon():
    connect()
    myCommonList.delete_many({})
    # 新增通用句
    common_registered = ['之前我們有讀過X的故事喔，現在你想聊聊哪本書呢', '我記得你有跟我分享過X的故事喔，這次你想聊聊哪本書呢']
    common_finished_T = ['上次我們聊過這本書囉~你想再跟我分享哪本新的故事呢？', '上次你跟我分享過這本書囉~你想聊聊哪本新的故事呢？']
    common_start = ['哈囉~你今天看了哪本書呢？', '你想跟我聊哪本書呢？', 'Hi~今天有甚麼有趣的故事書呢？']
    common_book_T = ['真巧！我剛好也看過這本書耶！', '我也看過這本書呢！']
    common_book_F = ['這本書我還沒看過欸，你想聊聊其他的書嗎？', '我好像沒看過這本書，你還有其他書可以跟我分享嗎？']
    common_finished_F = ['我記得這本書!上次我們有說到', '我記得上次你有告訴我', '我記得這個故事喔!上次我們有聊到故事中提到']
    common_prompt = ['可以跟我說說故事裡發生了什麼事嗎？', '可以告訴我故事裡的角色發生了甚麼事嗎？']
    common_match_T = ['哦~原來如此', '你講得很好呢！', '你說的對~', '你說的很好唷~']
    common_retrieve = ['我還知道', '我也看到', '故事中還有提到', '我還有看到']
    common_conj = [' 然後 ', ' 接下來 ', ' 而且 ', ' 接著 ', ' 後來 ']
    common_repeat = ['那接下來又發生了甚麼事呢？', '那之後還發生了甚麼事呢？', '接下來故事中還提到了甚麼呢？', '你可以再告訴我之後的故事嗎？', '你能再跟我分享接下來的故事嗎？']
    # 比對不到 進入Inqurie
    common_QA = ['別的小朋友也講過類似的事情，他告訴我', '我有聽過類似的故事']
    common_match_F = ['我不知道這件事耶，可以告訴我發生了甚麼事嗎？', '我好像沒看到這部分耶，你可以說說看你的想法嗎？', '我不知道有這個事情耶？你可以告訴我嗎',
                      '你說的事我沒聽過欸, 你可以更詳細一點告訴我嗎？']
    common_return = ['前面的故事還有提到', '前面我還知道', '故事前面還有']
    common_expand = ["看來你對這本書已經很熟悉了呢! 我們來聊聊你的心得吧", "你很了解這個故事呢! 那我們來互相分享心得吧", "你對這本書很熟悉呢! 那我們來說說你對故事的感想吧"]
    common_like = ["你喜歡這本書嗎", "你喜歡這個故事嗎", "你喜歡書裡的內容嗎"]
    common_like_response = ["我也喜歡這本書呢! 書裡的劇情很吸引我~", "我也喜歡這個故事呢! 我覺得這本書裡的角色很可愛也很有趣~"]
    common_like_expand = ["可以跟我分享你喜歡書裡的哪個部分嗎?", "那書裡的哪個部分吸引到你呢?", "那你喜歡書裡的哪個地方呢?"]
    common_feedback = ["哦哦原來如此~ 我對這本書的感想是XXX", "哦哦原來如此~ 其他小朋友和我分享過他們覺得XXX"]
    common_like_T = ["你喜歡這類型的書的話, 我可以推薦你XX這本書, 他也是關於OO的故事唷~", "那推薦你XX這本書, 書中也是描述關於OO的故事唷~說不定你也會喜歡呢!"]
    common_like_F = ["那我可以推薦你看看XX這本書, 他是另一個不同類型的故事, 說不定你會喜歡唷", "那你可以讀讀看XX這本書, 他是另一個不同類型的故事, 說不定你會喜歡呢",
                     "那你可以去讀讀看另一種類型的故事，像是XX這本書, 說不定你會喜歡唷"]
    common = [common_registered, common_start, common_book_T, common_finished_T, common_finished_F, common_book_F,
              common_prompt, common_repeat, common_conj, common_match_T, common_match_F, common_QA, common_retrieve,
              common_return, common_expand, common_like, common_like_response, common_like_expand, common_feedback, common_like_T,
              common_like_F]
    common_type = ["common_registered", "common_start", "common_book_T", "common_finished_T", "common_finished_F",
                   "common_book_F", "common_prompt", "common_repeat", "common_conj", "common_match_T", "common_match_F",
                   "common_QA", "common_retrieve", "common_return", "common_expand", "common_like", "common_like_response", "common_like_expand", "common_feedback",
                   "common_like_T", "common_like_F"]

    for i in range(len(common)):
        common_dict = {'type': common_type[i], 'content': common[i]}
        myCommonList.insert_one(common_dict)
        print(common_dict)


# 新增故事書SVO data
def addBookInfo(bookName, c1, verb, c2, sentence, sentence_Translate, sentenceID, speaker, speak_to):
    # 連接mongo
    myClient = pymongo.MongoClient("mongodb://140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    myVerbList = myBook.VerbTable

    mydict = {'Sentence_id': sentenceID, 'C1': c1, 'Verb': verb, 'C2': c2, 'Sentence': sentence,
              'Sentence_translate': sentence_Translate, 'Speaker': speaker, 'Speak_to': speak_to}
    myVerbList.insert(mydict)
    print(mydict)


def addBookKeyword(bookName, entityList, verbList):
    # 連接mongo
    myClient = pymongo.MongoClient("mongodb://140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    myKeyList = myBook.KeywordTable

    mydict = {'Entity_List': entityList, 'Verb_List': verbList}
    myKeyList.insert(mydict)
    print(mydict)


def updateUser(userId, bookName, record_list, match_entity, match_verb, state):
    # 連接mongo

    myClient = pymongo.MongoClient("mongodb://140.115.53.196:27017/")
    myBotData = myClient.Chatbot
    myUserList = myBotData.UserTable
    bookTalkSummary = {'Sentence_id_list': record_list, 'Entity_list': match_entity,
                       'Verb_list': match_verb, 'Finish': state}

    if not list(myUserList.find()):
        # 資料庫無資料 > 直接新增一筆
        mydict = {'User_id': userId, 'BookTalkSummary': {bookName: bookTalkSummary}}
        myUserList.insert(mydict)
    else:
        find_user = {'User_id': userId}
        now_user = myUserList.find_one(find_user)
        # 若沒有該使用者之資料
        if now_user is None:
            # 直接新增一筆
            mydict = {'User_id': userId, 'BookTalkSummary': {bookName: bookTalkSummary}}
            myUserList.insert(mydict)
        # 有該使用者資料
        else:
            if bookName in now_user['BookTalkSummary']:
                # 有該本書之資料 > 更新內容
                user_book_result = copy.deepcopy(now_user)
                for book_data in user_book_result['BookTalkSummary'].keys():
                    if book_data == bookName:
                        user_book_result['BookTalkSummary'][book_data] = bookTalkSummary
                myUserList.update_one(find_user, {"$set": user_book_result})
            else:
                # 同一筆資料下新增key值
                user_book_result = copy.deepcopy(now_user)
                user_book_result['BookTalkSummary'].update({bookName: bookTalkSummary})
                myUserList.update_one(find_user, {"$set": user_book_result})


def addDialog(bookName, session_id, dialog_id, speaker_id, content, time):
    myClient = pymongo.MongoClient("mongodb://140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    allDialog = myBook.S_R_Dialog

    mydict = {'Session_id': session_id, 'Dialog_id': dialog_id, 'Speaker_id': speaker_id, 'Content': content,
              'Time': time}
    allDialog.insert(mydict)
    print(mydict)


def addQuestion(bookName, qa_id, dialog_id, response):
    myClient = pymongo.MongoClient("mongodb://140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    QATable = myBook.QATable

    mydict = {'QA_id': qa_id, 'Dialog_id': dialog_id, 'Response': response}
    QATable.insert(mydict)
    print(mydict)


def addElaboration(bookName, qa_id, elaboration, confidence, sentence_id):
    myClient = pymongo.MongoClient("mongodb://140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    Elaboration_Table = myBook.Elaboration

    mydict = {'QA_id': qa_id, 'Elaboration': elaboration, 'Confidence': confidence, 'Sentence_id': sentence_id}
    Elaboration_Table.insert(mydict)
    print(mydict)


if __name__ == "__main__":
    addCommon()
