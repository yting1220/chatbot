# 建立故事內容及關鍵字資料庫
import pymongo
from allennlp.predictors.predictor import Predictor
import copy
from nltk.stem import WordNetLemmatizer
from googletrans import Translator
import createLibrary
story_name = ""
content_list = []
words = []
entityInfo = {}


def createStory():
    global words
    path = "story/" + story_name + ".txt"
    f = open(path, mode='r')
    words = f.read()
    story_content = words.replace('*', '').replace('\n', ' ')
    createLibrary.addBook(story_name, story_content)
    f.close()


def coReference():
    # 紀錄每個角色出現次數
    # tempMax = 0
    # tempProtagonist = ''
    global content_list, entityInfo
    createStory()
    content = words.replace('\n', ' ')
    predictor = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/coref-spanbert-large-2020.02.27.tar.gz")
    result_1 = predictor.predict(
        document=content
    )
    result = copy.deepcopy(result_1)

    content_list = result['document']
    # 找出代名詞對應主詞 修改原文
    delchar = ['a ', 'the ', 'A ', "The "]
    for i in range(len(result['clusters'])):
        count = 0
        temp_name = ' '.join(result['document'][result['clusters'][i][0][0]:result['clusters'][i][0][1] + 1])
        # 額外處理
        if story_name == "Fairy friends" and temp_name == 'Patch , a bad elf':
            temp_name = 'Patch'
        if story_name == 'Hansel and Gretel' and temp_name == 'I':
            temp_name = 'Hansel'
        if story_name == 'Drop It, Rocket!' and temp_name == 'I':
            temp_name = 'Owl'
        if story_name == 'Rocket and the Perfect Pumpkin' and temp_name == 'you':
            temp_name = 'Rocket'
        if story_name == 'Rocket and the Perfect Pumpkin' and temp_name == 'me':
            temp_name = 'Bella'
        if story_name == 'Shopping' and temp_name == 'He':
            temp_name = 'Chip'
        if story_name == "TY'S TRAVELS ALL Aboard!" and temp_name == 'My':
            temp_name = 'TY'
        if story_name == "TY'S TRAVELS ALL Aboard!" and temp_name == 'We':
            temp_name = 'TY, Daddy and Mom'
        for index in delchar:
            if temp_name[0:2] == index or temp_name[0:4] == index:
                temp_name = temp_name.replace(index, "")
        # print(temp_name)

        for j in result['clusters'][i]:
            count += 1
            # print(str(j) + ":" + str(result['document'][j[0]:j[1] + 1]), end=',')
            # print(' '.join(result['document'][j[0]:j[1] + 1]))
            # print("story_list", end=':')
            # print(content_list[j[0]])
            if j[0] == j[1]:
                content_list[j[0]] = temp_name
        # 計算出現次數最高者
        # if count > tempMax:
        #     tempMax = count
        # tempProtagonist = temp_name

        entityInfo[temp_name] = {"Frequence": count}
        # print("出現次數：" + str(count), end='\r\n\r\n')
    # print('主角出現'+str(tempMax) + "次：" + tempProtagonist + '\n')


def story_analysis():
    myClient = pymongo.MongoClient("mongodb://root:ltlab35316@140.115.53.196:27017/")
    myBook = myClient[story_name.replace(' ', '_').replace("'", "")]
    myVerbList = myBook.VerbTable
    myKeyList = myBook.KeywordTable
    coReference()
    wnl = WordNetLemmatizer()
    verbName = []
    verbInfo = {}
    storyPhraseList = words.replace('*', '').split('\n')

    story_2 = ' '.join(content_list)
    print(story_2)
    # *符號表示換行
    story_2 = story_2.replace(' * ', ' \r\n')
    story_2_PhraseList = story_2.split('\r\n')
    for i in story_2_PhraseList:
        print(i)

    # Dependency Parsing
    predictor = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")

    counter_speech = False

    for i in range(len(story_2_PhraseList)):
        c1_list = []
        c2_list = []
        v_list = []
        v = False
        if story_2_PhraseList[i].endswith(', '):
            sentence = story_2_PhraseList[i].replace(',', '')
        else:
            sentence = story_2_PhraseList[i].replace(' .', '')
        result = predictor.predict(
            sentence=sentence
        )
        print(sentence)
        # 抓出主要SVO
        svo = {}
        for j in range(len(result['pos'])):
            if v == False and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                if result['words'][j] not in c1_list:
                    c1_list.append(result['words'][j])
                continue
            if (result['pos'][j] == 'VERB' and result['predicted_dependencies'][j] != 'aux') or (
                    result['pos'][j] == 'AUX' and result['predicted_dependencies'][j] == 'root'):
                if result['words'][j].lower() != 'can':
                    v = True
                    if result['words'][j] not in v_list:
                        v_list.append(result['words'][j].lower())
                        # 找出動詞keyword
                        word = wnl.lemmatize(result['words'][j], 'v')
                        verbName.append(word.lower())
                continue
            if v == True and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                if result['words'][j] not in c2_list:
                    c2_list.append(result['words'][j])
                continue
        print('S:' + str(c1_list) + ' V:' + str(v_list) + ' O:' + str(c2_list))
        if len(c1_list) != 0:
            svo['C1'] = c1_list
        if len(v_list) != 0:
            svo['Verb'] = v_list
        if len(c2_list) != 0:
            svo['C2'] = c2_list

        speaker = ''
        speak_to = ''
        if '"' in story_2_PhraseList[i]:
            dialog_sentence = story_2_PhraseList[i].replace(' . ', '')
            counter_speech_ind = i
            if dialog_sentence.startswith('" '):
                dialog_list = dialog_sentence.split(' " ')
                if len(dialog_list) == 1:
                    # 說話者為空
                    speaker = ''
                else:
                    match = False
                    if ', ' in dialog_list[1]:
                        temp = dialog_list[1].split(", ")[0].split(" ")
                    else:
                        temp = dialog_list[1].split(" ")
                    for d_index in range(len(temp)):
                        for index in range(len(v_list)):
                            if temp[d_index] == v_list[index]:
                                match = True
                                if d_index == 0:
                                    # "" say XXX
                                    speaker = ' '.join(temp[1:])
                                else:
                                    # "" XXX say
                                    speaker = ' '.join(temp[0:d_index])
                                    # 改寫原句 將對話句子的說話者代名詞改為角色名稱
                                    temp_phrase = storyPhraseList[i].split('" ')[1].split(' ' + temp[d_index])[0]
                                    storyPhraseList[i] = storyPhraseList[i].replace(" " + temp_phrase + " ",
                                                                                    " " + speaker + ' ')
                                    print(storyPhraseList[i])
                                break
                        if match:
                            break
            else:
                # XXX say ""
                match = False
                dialog_list = dialog_sentence.split(', " ')
                if ', ' in dialog_list[0]:
                    temp = dialog_list[0].split(", ")[1].split(" ")
                else:
                    temp = dialog_list[0].split(" ")
                for d_index in range(len(temp)):
                    for index in range(len(v_list)):
                        if temp[d_index] == v_list[index]:
                            match = True
                            speaker = ' '.join(temp[0:d_index])
                            # 改寫原句 將對話句子的說話者代名詞改為角色名稱
                            temp_phrase = storyPhraseList[i].split(' "')[0].split(' ' + temp[d_index])[0]
                            storyPhraseList[i] = storyPhraseList[i].replace(" " + temp_phrase + " ",
                                                                            " " + speaker + ' ')
                            print(storyPhraseList[i])
                            break
                    if match:
                        break
            # speak_to
            if counter_speech and (i - counter_speech_ind) == 1:
                speak_to = counter_speech_ind - 1
            elif counter_speech and (i - counter_speech_ind) != 1:
                if speaker in story_2_PhraseList[i]:
                    speak_to = counter_speech_ind - 1

            counter_speech = True
        else:
            counter_speech = False

        translator = Translator()
        while True:
            try:
                sentence_Translate = translator.translate(storyPhraseList[i], src="en", dest="zh-TW").text
                # 額外處理翻譯問題
                if story_name == "Fairy friends":
                    missing_patch = ['補丁', '帕奇']
                    missing_fairy = ['仙女', '童話']
                    for word in missing_patch:
                        sentence_Translate = sentence_Translate.replace(word, 'Patch')
                    for word in missing_fairy:
                        sentence_Translate = sentence_Translate.replace(word, '精靈')
                if story_name == 'Hansel and Gretel':
                    sentence_Translate = sentence_Translate.replace('a夫', '樵夫')
                if story_name == 'A Monster is Coming!':
                    missing_Inchworm = ['九蟲', 'ch蟲', '尺ch']
                    for word in missing_Inchworm:
                        sentence_Translate = sentence_Translate.replace(word, '蟲')
                    sentence_Translate = sentence_Translate.replace('Baby Bug', '寶貝蟲')
                    sentence_Translate = sentence_Translate.replace('Bug', '蟲子')
                if story_name == 'Drop It, Rocket!' or story_name == 'Rocket and the Perfect Pumpkin' or story_name == 'Rocket the Brave!' or story_name == "Rocket's 100th Day of School":
                    sentence_Translate = sentence_Translate.replace('火箭', 'Rocket')
                if story_name == 'Jack and Jill and T-Ball Bill':
                    sentence_Translate = sentence_Translate.replace('賬單', '比爾')
                if story_name == 'The chase':
                    sentence_Translate = sentence_Translate.replace('軟盤', 'Floppy')
                break
            except Exception as e:
                print(e)

        if speaker != '' and sentence_Translate.startswith('“'):
            temp = sentence_Translate.split('”')
            temp.reverse()
            sentence_Translate = ''.join(temp)

        sentence_info = {'Sentence_Id': i, 'Sentence': story_2_PhraseList[i],
                         'Sentence_translate': sentence_Translate, 'Speaker': speaker, 'Speak_to': speak_to}
        mydict = svo.copy()
        mydict.update(sentence_info)
        myVerbList.insert_one(mydict)
        print(mydict)

    for index in verbName:
        verbInfo[index] = {"Frequence": verbName.count(index)}
    myKeyDict = {'Entity_list': entityInfo, 'Verb_list': verbInfo}
    myKeyList.insert_one(myKeyDict)
    print(myKeyDict)


if __name__ == "__main__":
    story_analysis()
    # coReference()
    # createStory()
