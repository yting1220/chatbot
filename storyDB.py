# 建立故事內容及關鍵字資料庫
from allennlp.predictors.predictor import Predictor
import copy
from nltk.stem import WordNetLemmatizer
from googletrans import Translator
import createLibrary

# 目前書單 >> "Fairy friends": "精靈", "Sleeping Beauty": "公主"
story_name = "Fairy friends"
story_type = "精靈"
content_list = []
words = []
entityInfo = {}
entity_list = []
main_entity = []


def createStory():
    global words
    createLibrary.addBook(story_name, story_type)
    path = "story/" + story_name + ".txt"
    f = open(path, mode='r')
    words = f.read()
    f.close()


def coReference():
    # 紀錄每個角色出現次數
    # tempMax = 0
    # tempProtagonist = ''
    global content_list, entityInfo, entity_list, main_entity
    sort_entity = {}
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
    for i in range(len(result['clusters'])):
        count = 0
        temp_name = ' '.join(result['document'][result['clusters'][i][0][0]:result['clusters'][i][0][1] + 1])
        # 額外處理
        if story_name == "Fairy friends" and temp_name == 'Patch , a bad elf':
            temp_name = 'Patch'
        temp_name = temp_name.replace("a ", "").replace("the ", "").replace("The ", "").replace("A ", "")
        entity_list.append(temp_name)
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
        sort_entity[temp_name] = count
        # print("出現次數：" + str(count), end='\r\n\r\n')
    # print('主角出現'+str(tempMax) + "次：" + tempProtagonist + '\n')

    # 排序entity 判斷出現次數高者為主要角色
    main_entity = []
    sort_entity = sorted(sort_entity.items(), key=lambda x: x[1], reverse=True)
    temp = int(len(sort_entity) * 0.3)
    for i in sort_entity[:temp]:
        main_entity.append(i[0])


def story_analysis():
    coReference()
    wnl = WordNetLemmatizer()
    verbName = []
    verbInfo = {}
    contain_keyword = False

    storyPhraseList = words.split('\n')

    story_2 = ' '.join(content_list)
    story_2 = story_2.replace(' . ', ' . \r\n')
    if story_name == "Fairy friends":
        story_2 = story_2.replace('mouse ! mouse', 'mouse.\r\nmouse').replace('elf ! Patch', 'elf.\r\nPatch').replace(
            'Patch . \r\nGo away', 'Patch . Go away').replace('elf ! " Lily', 'elf ! " \r\nLily').replace('too ! " fairy', 'too !\r\n" fairy')
    if story_name == "Sleeping Beauty":
        story_2 = story_2.replace('die . \r\nbaby', 'die . baby').replace('years . \r\n"', 'years . " \r\n')
    if story_name == 'Hansel and Gretel':
        story_2 = story_2.replace(' . \r\n" " Then', ' . " \r\n" Then').replace(' . \r\n"', ' . "\r\n')
    story_2_PhraseList = story_2.split('\r\n')
    print(story_2_PhraseList)

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
        for j in range(len(result['pos'])):
            if v == False and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                if result['words'][j] not in c1_list:
                    c1_list.append(result['words'][j])
                    for index in main_entity:
                        if result['words'][j] in index:
                            contain_keyword = True
                continue
            if result['pos'][j] == 'VERB' and result['predicted_dependencies'][j] != 'aux':
                if result['words'][j].lower() != 'will' and result['words'][j].lower() != 'can':
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
                    for index in main_entity:
                        if result['words'][j] in index:
                            contain_keyword = True
                continue
        print('S:' + str(c1_list) + ' V:' + str(v_list) + ' O:' + str(c2_list))

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
                                    temp_phrase = storyPhraseList[i].split('" ')[1].split(' '+temp[d_index])[0]
                                    storyPhraseList[i] = storyPhraseList[i].replace(" " + temp_phrase + " ", " " + speaker+' ')
                                    print(storyPhraseList[i])
                                break
                        if match:
                            break
            else:
                # XXX say ""
                match = False
                dialog_list = dialog_sentence.split(', " ')
                temp = dialog_list[0].split(" ")
                for d_index in range(len(temp)):
                    for index in range(len(v_list)):
                        if temp[d_index] == v_list[index]:
                            match = True
                            speaker = ' '.join(temp[0:d_index])
                            # 改寫原句 將對話句子的說話者代名詞改為角色名稱
                            temp_phrase = storyPhraseList[i].split(' "')[0].split(' '+temp[d_index])[0]
                            storyPhraseList[i] = storyPhraseList[i].replace(" " + temp_phrase + " ", " " + speaker+' ')
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
            print("說話者："+speaker)
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
                break
            except Exception as e:
                print(e)

        createLibrary.addBookInfo(story_name, c1_list, v_list, c2_list, story_2_PhraseList[i], sentence_Translate, i, speaker, speak_to, contain_keyword)
        contain_keyword = False

    for index in verbName:
        verbInfo[index] = {"Frequence": verbName.count(index)}
    createLibrary.addBookKeyword(story_name, entityInfo, verbInfo)


if __name__ == "__main__":
    story_analysis()
