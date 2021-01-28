# 建立故事內容及關鍵字資料庫
from allennlp.predictors.predictor import Predictor
import copy
from nltk.stem import WordNetLemmatizer
from googletrans import Translator
import createLibrary

story_name = "Hansel and Gretel"
story_type = "小孩"
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
    delchar = ['a ', 'the ', 'A ', "The "]
    for i in range(len(result['clusters'])):
        count = 0
        temp_name = ' '.join(result['document'][result['clusters'][i][0][0]:result['clusters'][i][0][1] + 1])
        # 額外處理
        if story_name == "Fairy friends" and temp_name == 'Patch , a bad elf':
            temp_name = 'Patch'
        for index in delchar:
            if temp_name[0:2] == index or temp_name[0:4] == index:
                temp_name = temp_name.replace(index, "")
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

    storyPhraseList = words.split('\n')

    story_2 = ' '.join(content_list)
    print(story_2)
    story_2 = story_2.replace(' . ', ' . \r\n')
    if story_name == "Fairy friends":
        story_2 = story_2.replace('mouse ! mouse', 'mouse.\r\nmouse').replace('elf ! Patch', 'elf.\r\nPatch').replace(
            'Patch . \r\nGo away', 'Patch . Go away').replace('elf ! " Lily', 'elf ! " \r\nLily').replace('too ! " fairy', 'too !\r\n" fairy')
    if story_name == "Sleeping Beauty":
        story_2 = story_2.replace('die . \r\nbaby', 'die . baby').replace('years . \r\n"', 'years . " \r\n')
    if story_name == "The Tale of Jemima Puddle-Duck":
        story_2 = story_2.replace('safe . \r\n" ', 'safe . "\r\n').replace('nest . \r\nJemima', 'nest . Jemima').replace('dinner . \r\n" ', 'dinner . "\r\n').replace('shed . \r\n" ', 'shed . "\r\n')
    if story_name == "Puss in Boots":
        story_2 = story_2.replace('partridges . \r\n" ', 'partridges . "\r\n').replace('river . \r\n" ', 'river . "\r\n').replace('taken . \r\n" ', 'taken . "\r\n').replace('home . \r\n" ', 'home . "\r\n').replace('men master . \r\n" ', 'men master . "\r\n')\
            .replace('? " ', '? "\r\n').replace('mouse . \r\n" ', 'mouse . "\r\n').replace('gifts . \r\nHow', 'gifts . How').replace('? "\r\nsaid', '? " said').replace('bag . \r\n" ', 'bag . "\r\n')
    if story_name == "Little Red Riding Hood":
        story_2 = story_2.replace(' " " ', ' "\r\n" ').replace('up ! " ', 'up ! "\r\n').replace('closer . \r\n" ', 'closer . "\r\n')
    if story_name == "The Magic Paintbrush":
        story_2 = story_2.replace('wood . \r\nSui', 'wood . Sui').replace('bedroom ! ', 'bedroom ! \r\n').replace('face ! ', 'face ! \r\n').replace('magic ! ', 'magic ! \r\n').replace('people . \r\n" ', 'people . "\r\n').replace('snakes ! ', 'snakes ! \r\n').replace('go ! " ', 'go ! "\r\n').replace('money . \r\n" ', 'money . "\r\n').replace('Ming . \r\n" In', 'money . "\r\nIn')
    if story_name == "Hansel and Gretel":
        story_2 = story_2.replace('eat . \r\n" ', 'eat . "\r\n').replace('wood . \r\n" ', 'wood . "\r\n').replace('must . \r\n" ', 'must . "\r\n').replace('take . \r\n" ', 'take . "\r\n').replace('home . \r\n" ', 'home . "\r\n').replace('fire . \r\n" ', 'fire . "\r\n').replace('money . \r\n" ', 'money . "\r\n').replace('left . \r\n', 'left . ')
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
        for j in range(len(result['pos'])):
            if v == False and (result['pos'][j] == 'PROPN' or result['pos'][j] == 'NOUN'):
                if result['words'][j] not in c1_list:
                    c1_list.append(result['words'][j])
                continue
            if (result['pos'][j] == 'VERB' and result['predicted_dependencies'][j] != 'aux') or (result['pos'][j] == 'AUX' and result['predicted_dependencies'][j] == 'root'):
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

        if speaker != '' and sentence_Translate.startswith('“'):
            temp = sentence_Translate.split('”')
            temp.reverse()
            sentence_Translate = ''.join(temp)
        createLibrary.addBookInfo(story_name, c1_list, v_list, c2_list, story_2_PhraseList[i], sentence_Translate, i, speaker, speak_to)

    for index in verbName:
        verbInfo[index] = {"Frequence": verbName.count(index)}
    createLibrary.addBookKeyword(story_name, entityInfo, verbInfo)


if __name__ == "__main__":
    story_analysis()
    # coReference()
    # createStory()