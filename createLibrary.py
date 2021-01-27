# 建立通用句及書單資料庫
import copy
import os
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
        myclient = pymongo.MongoClient("mongodb://root:ltlab35316@140.115.53.196:27017/")

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
    path = "common_list/"
    allList = os.listdir(path)
    for file in allList:
        common_phrase = []
        file_path = path + file
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                for line in f:
                    common_phrase.append(line.replace('\n', ''))
            common_dict = {'type': file.replace('.txt', ''), 'content': common_phrase}
            myCommonList.insert_one(common_dict)
            print(common_dict)


# 新增故事書SVO data
def addBookInfo(bookName, c1, verb, c2, sentence, sentence_Translate, sentenceID, speaker, speak_to):
    # 連接mongo
    myClient = pymongo.MongoClient("mongodb://root:ltlab35316@140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    myVerbList = myBook.VerbTable

    mydict = {'Sentence_id': sentenceID, 'C1': c1, 'Verb': verb, 'C2': c2, 'Sentence': sentence,
              'Sentence_translate': sentence_Translate, 'Speaker': speaker, 'Speak_to': speak_to}
    myVerbList.insert(mydict)
    print(mydict)


def addBookKeyword(bookName, entityList, verbList):
    # 連接mongo
    myClient = pymongo.MongoClient("mongodb://root:ltlab35316@140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    myKeyList = myBook.KeywordTable

    mydict = {'Entity_List': entityList, 'Verb_List': verbList}
    myKeyList.insert(mydict)
    print(mydict)


def updateUser(userId, bookName, record_list, match_entity, match_verb, state):
    # 連接mongo

    myClient = pymongo.MongoClient("mongodb://root:ltlab35316@140.115.53.196:27017/")
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
    myClient = pymongo.MongoClient("mongodb://root:ltlab35316@140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    allDialog = myBook.S_R_Dialog

    mydict = {'Session_id': session_id, 'Dialog_id': dialog_id, 'Speaker_id': speaker_id, 'Content': content,
              'Time': time}
    allDialog.insert(mydict)
    print(mydict)


def addQuestion(bookName, qa_id, dialog_id, response):
    myClient = pymongo.MongoClient("mongodb://root:ltlab35316@140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    QATable = myBook.QATable

    mydict = {'QA_id': qa_id, 'Dialog_id': dialog_id, 'Response': response}
    QATable.insert(mydict)
    print(mydict)


def addElaboration(bookName, qa_id, elaboration, confidence, sentence_id):
    myClient = pymongo.MongoClient("mongodb://root:ltlab35316@140.115.53.196:27017/")
    myBook = myClient[bookName.replace(' ', '_')]
    Elaboration_Table = myBook.Elaboration

    mydict = {'QA_id': qa_id, 'Elaboration': elaboration, 'Confidence': confidence, 'Sentence_id': sentence_id}
    Elaboration_Table.insert(mydict)
    print(mydict)


if __name__ == "__main__":
    addCommon()
