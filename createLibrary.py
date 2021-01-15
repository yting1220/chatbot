# 建立通用句及書單資料庫
import copy

import pymongo
from googletrans import Translator
myClient: object
myClientData: object
myBookList: object
myCommonList: object


def connect():
    global myClient, myClientData, myBookList, myCommonList
    try:
        # 連接mongo
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")

        myClientData = myclient.client_data
        myBookList = myClientData.bookList
        myCommonList = myClientData.commonList
    except Exception as e:
        print(e)
    return myBookList, myCommonList


def addBook(bookName, bookType):
    connect()
    # 新增書單
    translator = Translator()
    book_dict = {'type': bookType, 'bookName': bookName,
                 'bookNameTranslate': translator.translate(bookName, src="en", dest="zh-TW").text}
    myBookList.insert_one(book_dict)
    print(book_dict)


def addCommon():
    connect()
    myCommonList.delete_many({})
    # 新增通用句
    common_combine = [' 還有 ', ' 和 ', ' 跟 ']
    common_bookRecord = ['之前我們有讀過X的故事喔，現在你想聊聊哪本書呢', '我記得你有跟我分享過X的故事喔，這次你想聊聊哪本書呢']
    commom_book_finish = ['上次我們聊過這本書囉~你想再跟我分享哪本新的故事呢？', '上次你跟我分享過這本書囉~你想聊聊哪本新的故事呢？']
    common_start = ['哈囉~你今天看了哪本書呢？', '你想跟我聊哪本書呢？', 'Hi~今天有甚麼有趣的故事書呢？']
    common_start_checkO = ['真巧！我剛好也看過這本書耶！', '我也看過這本書呢！']
    common_start_checkX = ['這本書我還沒看過欸，你想聊聊其他的書嗎？', '我好像沒看過這本書，你還有其他書可以跟我分享嗎？']
    common_book_second = ['我記得這本書!上次我們有說到', '我記得上次你有告訴我', '我記得這個故事喔!上次我們有聊到故事中提到']
    common_prompt = ['可以跟我說說故事裡發生了什麼事嗎？', '可以告訴我故事裡的角色發生了甚麼事嗎？']
    common_prompt_secondLogin = ['那之後還發生了甚麼事呢？', '接下來故事中還提到了甚麼呢？', '你可以再告訴我之後的故事嗎？', '你能再跟我分享接下來的故事嗎?']
    common_evaluate = ['哦~原來如此', '你講得很好呢！', '你說的對~', '你說的很好唷~']
    common_follow = ['我還知道', '我也看到', '故事中還有提到', '我還有看到']
    common_conj = [' 然後 ', ' 接下來 ', ' 而且 ', ' 接著 ', ' 後來 ']
    common_repeat = ['那接下來又發生了甚麼事呢？']
    # 比對不到 進入Inqurie
    common_prompt_checkO = ['別的小朋友也講過類似的事情，他告訴我', '我有聽過類似的故事', '哦~原來如此']
    common_prompt_checkX = ['我不知道這件事耶，可以告訴我發生了甚麼事嗎？', '我好像沒看到這部分耶，你可以說說看你的想法嗎？', '我不知道有這個事情耶？你可以告訴我嗎',
                            '你說的事我沒聽過欸, 你可以更詳細一點告訴我嗎？']
    common_prompt_return = ['前面的故事還有提到', '前面我還知道', '故事前面還有']
    common_inqurie_new = ['哦哦哦我知道了~', '原來如此~我了解了']
    common_grow_check = ['你的意思是指X嗎', '你是要說X嗎', '你是在說X嗎']
    common_prompt_duplicate = ['你剛剛說過一樣的故事了唷']
    common_expand = ["看來你對這本書已經很熟悉了呢! 我們來聊聊你的心得吧", "你很了解這個故事呢! 那我們來互相分享心得吧", "你對這本書很熟悉呢! 那我們來說說你對故事的感想吧"]
    common_expand_student = ["你喜歡這本書嗎", "你喜歡這個故事嗎", "你喜歡書裡的內容嗎"]
    common_expand_chatbot = ["我也喜歡這本書呢! 書裡的劇情很吸引我~", "我也喜歡這個故事呢! 我覺得這本書裡的角色很可愛也很有趣~"]
    common_expand_chatbot_ask = ["可以跟我分享你喜歡書裡的哪個部分嗎?", "那書裡的哪個部分吸引到你呢?", "那你喜歡書裡的哪個地方呢?"]
    common_expand_chatbot_data = ["哦哦原來如此~ 我對這本書的感想是XXX", "哦哦原來如此~ 其他小朋友和我分享過他們覺得XXX"]
    common_suggestion_o = ["你喜歡這類型的書的話, 我可以推薦你XX這本書, 他也是關於OO的故事唷~", "那推薦你XX這本書, 書中也是描述關於OO的故事唷~說不定你也會喜歡呢!"]
    common_suggestion_x = ["那我可以推薦你看看XX這本書, 他是另一個不同類型的故事, 說不定你會喜歡唷", "那你可以讀讀看XX這本書, 他是另一個不同類型的故事, 說不定你會喜歡呢", "那你可以去讀讀看另一種類型的故事，像是XX這本書, 說不定你會喜歡唷"]
    common = [common_combine, common_bookRecord, commom_book_finish, common_start, common_start_checkO, common_start_checkX, common_book_second, common_prompt, common_prompt_secondLogin, common_evaluate, common_follow,
              common_conj, common_repeat, common_prompt_checkO, common_prompt_checkX, common_prompt_return, common_inqurie_new, common_grow_check, common_prompt_duplicate, common_expand, common_expand_student,
              common_expand_chatbot, common_expand_chatbot_ask, common_expand_chatbot_data, common_suggestion_o, common_suggestion_x]
    common_type = ["common_combine", "common_bookRecord", "commom_book_finish", "common_start", "common_start_checkO", "common_start_checkX", "common_book_second", "common_prompt", "common_prompt_secondLogin", "common_evaluate",
                   "common_follow", "common_conj", "common_repeat", "common_prompt_checkO", "common_prompt_checkX", "common_prompt_return", "common_inqurie_new", "common_grow_check", "common_prompt_duplicate",
                   "common_expand", "common_expand_student", "common_expand_chatbot", "common_expand_chatbot_ask", "common_expand_chatbot_data", "common_suggestion_o", "common_suggestion_x"]

    for i in range(len(common)):
        common_dict = {'type': common_type[i], 'content': common[i]}
        myCommonList.insert_one(common_dict)
        print(common_dict)


# 新增故事書SVO data
def addBookInfo(bookName, c1, verb, c2, sentence, sentence_Translate, sentenceID, speaker, speak_to, contain_keyword):
    # 連接mongo
    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    myVerbList = myBook.VerbTable

    mydict = {'Sentence_id': sentenceID, 'C1': c1, 'Verb': verb, 'C2': c2, 'Sentence': sentence,
              'sentence_Translate': sentence_Translate, 'Speaker': speaker, 'Speak_to': speak_to,
              'Contain_keyword': contain_keyword}
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


def updateUser(userId, bookName, record_list, match_entity, match_verb, state):
    # 連接mongo

    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myClientData = myClient.client_data
    myUserList = myClientData.userTable
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
    myClient = pymongo.MongoClient("mongodb://localhost:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    allDialog = myBook.S_R_Dialog

    mydict = {'Session_id': session_id, 'Dialog_id': dialog_id, 'Speaker_id': speaker_id, 'Content': content,
              'Time': time}
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
    addCommon()
