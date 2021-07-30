from tkinter import *
import json
import os
import sys
import webbrowser

# Your yago_code.py "output" folder
#directory = 'C:/Users/kulbe/Downloads/yago_graph/output/' # Yago_graph
#directory = 'C:/Users/kulbe/Downloads/output/' # Single layer demo 1
directory = 'source/output/' # YAGO REFACTOR
#directory = 'outputRecord/' # YAGO REFACTOR (SAVED)
#directory = '/outputCollated/' # YAGO REFACTOR Collated
logging = True
test = False

"""
WHAT IT DOES
Checks for duplicate topic keys/titles and link keys, and visualizes node links (down layers only, not up)
This is for use on Tashlin's yago_code.py "output" folder
- And more recently the collated files (that will need to be in their own folder)

HOW TO USE
Update the directory location and call dupe_test(GUI, exception)
- GUI is boolean: True means show the GUI, False will only run the duplicate tests
- exception is boolean: True will throw exceptions for duplicates, False will only output to console
To run locally simply update directory and run the file, output will be in the console and GUI
To use as an in-line dupe checker simply call dupe_test(GUI, True)
- Return 0 means no duplicates (If GUI is True will only return after GUI is closed, for manual review)
- Try-catch exceptions or your code will crash in case of duplicates

EXCEPTIONS
The exception main argument enables custom exceptions for use in the calling function
- 'DUPLICATE TOPIC KEY', 'DUPLICATE TOPIC TITLE', 'DUPLICATE LINK KEY', 'DUPLICATE LINK PATH', 'SELF-REFERENTIAL LINK'
There's also a custom directory exception 'UNKNOWN FILE TYPE' in case of bad directory. Not optional

GUI
Search by unique topic key or name (case sensitive). Enter key works
Results are split by link type, "has" links will display their values
Reds are duplicates or self-referentials. This is determined fresh each search, the graph is NOT rebuilt
"""


class Topic: #Define Topics as their titles, ie Animals = Topic(key, type)
    def __init__(self, dict):
        self.args = dict
        self.links = {}

class Link: #Define Links as their types, ie hasInstance = Link()
    def __init__(self, type, name):
        self.type = type
        self.name = name
        self.listSource = []
        self.listTarget = []

    def link(self, source, target):
        self.listSource.append(source)
        self.listTarget.append(target)
        if self in source.links:
            source.links[self].append(target)
        else:
            source.links[self] = [target]

def printf(*args):
    restore = sys.stdout
    for i in args:
        print(i)
    if logging:
        with open(directory + 'DUPE_LOG.txt', 'a', encoding='utf-8') as f:
            sys.stdout = f
            for i in args:
                print(i)
            sys.stdout = restore

def dupe_test(GUI, exception):
    # Local graph init
    topic_graph = {}
    link_graph = {}

    ### FIND ALL FILES IN DIRECTORY
    entries = os.listdir(directory)
    topics = []
    links = []
    for entry in entries:
        if 'DUPE_LOG.txt' == entry:
            os.remove(directory + 'DUPE_LOG.txt')
        elif '.txt' in entry or '.zip' in entry or 'TODO.json' in entry:
            pass
        elif test:
            if 'TEST_topics' in entry:
                topics.append(entry)
            elif 'TEST_links' in entry:
                links.append(entry)
        elif 'TEST' in entry or 'refs' in entry:
            pass
        elif 'topics' in entry: # Sort out topic files
            topics.append(entry)
        elif 'links' in entry: # Sort out link files
            links.append(entry)
        elif 'unclustered' in entry: # Ignore, this is for other tracking
            pass
        else:
            printf('UNKNOWN FILE TYPE')
            raise Exception('UNKNOWN FILE TYPE') # Directory check


    ### ADD TOPICS TO LOCAL GRAPH AND CHECK FOR DUPLICATE KEYS/TITLES
    topic_list = {}
    dupes = {}
    for entry in topics:
        #print(entry)
        with open(directory + entry, 'r', encoding='utf8') as f:
            data = json.load(f)
            for i in data:
                flag = False
                if i['title'] in topic_list:
                    if i['_type'] in topic_list[i['title']]: # Duplicate titles are only okay for different types
                                    # This check does NOT prevent topic addition because otherwise links would break
                        for top in topic_graph:
                            if topic_graph[top].args['title'] == i['title']:
                                if topic_graph[top].args['reference']  == i['reference']:
                                    printf('DUPLICATE TOPIC TITLE ' + i['title'] + '; TYPE ' + i['_type'] + \
                                           '; KEYS ' + top + ' ' + i['_key'])
                                    if exception:
                                        raise Exception('DUPLICATE TOPIC TITLE')
                                elif not topic_graph[top].args['title'] in dupes:
                                    printf('DUPLICATE TOPIC FROM SOURCE ' + i['title'] + '; TYPE ' + i['_type'] +
                                           '; KEYS ' + top + ' ' + i['_key'])
                                    dupes[topic_graph[top].args['title']] = topic_graph[top].args['reference']
                                    if exception:
                                        raise Exception('DUPLICATE TOPIC FROM SOURCE')
                    else:
                        topic_list[i['title']].append(i['_type']) # Type records per title
                else:
                    topic_list[i['title']] = [i['_type']]
                if not i['_key'] in topic_graph: # Unique keys get added to local graph
                    key = i['_key']
                    del(i['_key'])
                    topic_graph[key] = Topic(i)
                else: # Duplicate keys get discarded, raise exceptions for handling wherever you called dupe_test
                    printf('DUPLICATE TOPIC KEY ' + i['_key'])
                    if exception:
                        raise Exception('DUPLICATE TOPIC KEY')

    ### LINKS
    link_list = []
    for entry in links:
        #print(entry)
        with open(directory + entry, 'r', encoding='utf8') as f:
            data = json.load(f)
            for i in data:
                flag = False
                if i['_type'] in link_graph:
                    if link_graph[i['_type']] in topic_graph[i['_from']].links: # Checks for duplicate link paths
                        if topic_graph[i['_to']] in topic_graph[i['_from']].links[link_graph[i['_type']]]:
                            if i['_type'] == 'has': # "has" can contain multiple entries of same title diff value
                                                    # ie "Alternate Name"
                                if i['name'] in topic_graph[i['_from']].args:
                                    if i['value'] in topic_graph[i['_from']].args[i['name']]:
                                        printf('DUPLICATE LINK PATH ' + i['_key']
                                              + '; FROM ' + i['_from'] + ':' + topic_graph[i['_from']].args['title']
                                              + ' > TO ' + i['_to'] + ':' + topic_graph[i['_to']].args['title'])
                                        flag = True
                                        if exception:
                                            raise Exception('DUPLICATE LINK PATH')
                            else:
                                printf('DUPLICATE LINK PATH ' + i['_key']
                                      + '; FROM ' + i['_from'] + ':' + topic_graph[i['_from']].args['title']
                                    + ' > TO ' + i['_to'] + ':' + topic_graph[i['_to']].args['title'])
                                flag = True
                                if exception:
                                    raise Exception('DUPLICATE LINK PATH')
                if i['_key'] in link_list:
                    printf('DUPLICATE LINK KEY ' + i['_key'])
                    flag = True
                    if exception:
                        raise Exception('DUPLICATE LINK KEY')
                if not i['_type'] in link_graph and not flag:
                    link_graph[i['_type']] = Link(i['_type'], i['name'])  # Add new link types (ie "has")
                    link_list.append(i['_key']) # Records link keys
                link_graph[i['_type']].link(topic_graph[i['_from']], topic_graph[i['_to']])  # See Link.link() above ^
                if i['_type'] == 'has' and not flag: # Only "has" has values, stored per topic
                    if i['name'] in topic_graph[i['_from']].args:
                        topic_graph[i['_from']].args[i['name']].append(i['value'])
                    else:
                        topic_graph[i['_from']].args[i['name']] = [i['value']]
                if i['_from'] == i['_to']:
                    printf('SELF-REFERENTIAL LINK ' + i['_key'] + '; TYPE ' + i['_type'] + '; TOPIC ' + i['_from'])
                    if exception:
                        raise Exception('SELF-REFERENTIAL LINK')


    # If false, only runs the dupe test. Everything after is for the GUI
    if not GUI:
        return 0

    ### DEBUG AND DATA SAMPLES
    """
    print('TOPIC GRAPH')
    print(topic_graph)
    print(topic_graph['T1'].args)
    print(topic_graph['T1'].links)
    print('LINK GRAPH')
    print(link_graph)
    print(link_graph['encompasses'].listSource)
    print(link_graph['encompasses'].listTarget)
    """

    ### GUI
    # Search button click event
    def searchClick():
        s = search.get()
        if s in topic_graph:
            return display(s)
        for i in topic_graph:
            if topic_graph[i].args['title'] == s:
                return display(i)
        n = Label(window, text='KEY NOT FOUND')
        n.place(x=10, y=40, width=300)

    def searchReturn(event):
        searchClick()

    def leftClick():
        if int(active[0][1:]) > 1:
            return display('T' + str(int(active[0][1:])-1))
        else:
            n = Label(window, text='INDEX BOUNDS ERROR')
            n.place(x=10, y=40, width=300)

    def rightClick():
        if int(active[0][1:]) < len(topic_graph):
            return display('T' + str(int(active[0][1:]) + 1))
        else:
            n = Label(window, text='INDEX BOUNDS ERROR')
            n.place(x=10, y=40, width=300)

    def webClick():
        webbrowser.open(topic_graph[active[0]].args['reference'], new=1, autoraise=True)

    items = [] # Logs GUI elements that need to be destroyed on new search
    def display(topic):
        active[0] = topic
        for i in items:
            i.destroy()
        items.clear()
        # Callable, dynamic storage for GUI elements
        dL = {} # Labels
        dS = {} # Separators
        dB = {} # Scrollbars and Listboxes
        h = 70 # Y value of items
        n = Label(window, text=topic+': '+topic_graph[topic].args['title']) # Search result topic node label (middle)
        n.place(x=10, y=40, width=300)

        if topic_graph[topic].args['_type'] == 'property': # TODO: Display "(origin)" for topics / clusters?
            dL[h] = Label(window, text='(origin)')  # Link type display (left)
            dL[h].place(x=10, y=h, width=100)
            items.append(dL[h])
            dB[h] = Scrollbar(window)  # Scrollbar instance per link type (right)
            dB[h].place(x=120, y=h, width=300)
            items.append(dB[h])
            dB[h + 1] = Listbox(window, yscrollcommand=dB[h].set)  # Listbox instance per link type (right)
            items.append(dB[h + 1])
            tempcount = 0
            hascount = {}
            for i in range(len(link_graph['has'].listTarget)):  # Iterates topics per link type for display
                top = link_graph['has'].listTarget[i]
                if topic_graph[topic].args['title'] == link_graph['has'].listTarget[i].args['title']:
                    if link_graph['has'].listSource[i].args['title'] in hascount:
                        hascount[link_graph['has'].listSource[i].args['title']] += 1
                        tempcount -= 20
                    else: # TODO: Display count
                        hascount[link_graph['has'].listSource[i].args['title']] = 1
                        dB[h + 1].insert(END, link_graph['has'].listSource[i].args['title'] + '\n')  # Items added to
                    tempcount += 20  # Tabulates required h change for number of items

            dB[h + 1].place(x=120, y=h, width=290, height=min(200, dB[h + 1].size() * 20))
            dB[h].config(command=dB[h + 1].yview)
            h += min(tempcount, 210)  # Limit h growth to size of scrollbox
            dS[h] = Label(window, text='_' * 410)
            dS[h].place(x=10, y=h, width=410)
            items.append(dS[h])
            h += 20

        else:
            for link in topic_graph[topic].links:  # Iterates link TYPES for chosen topic
                if link.type == 'Link':
                    dL[h] = Label(window, text='Link: '+link.name)  # Link type display (left)
                else:
                    dL[h] = Label(window, text=link.type)  # Link type display (left)
                dL[h].place(x=10, y=h, width=100)
                items.append(dL[h])
                dB[h] = Scrollbar(window)  # Scrollbar instance per link type (right)
                dB[h].place(x=120, y=h, width=300)
                items.append(dB[h])
                dB[h + 1] = Listbox(window, yscrollcommand=dB[h].set)  # Listbox instance per link type (right)
                items.append(dB[h + 1])
                tempcount = 0
                hascount = {}
                for top in topic_graph[topic].links[link]:  # Iterates topics per link type for display
                    flag = False
                    if top.args['title'] + '\n' in dB[h + 1].get(0, dB[h + 1].size() - 1):
                        flag = True  # Duplicate found (doesn't work for "has" b/c that displays property value)
                    if top.args['title'] == topic_graph[topic].args['title']:
                        if topic_graph[topic].args['_type'] == top.args['_type']:
                            flag = True  # Self-referential found
                    if link.type == 'has':  # "has" items
                        if top.args['title'] in hascount:
                            if not len(topic_graph[topic].args[top.args['title']])-1 == hascount[top.args['title']]:
                                hascount[top.args['title']] += 1
                        else:
                            hascount[top.args['title']] = 0
                        if top.args['title'] in topic_graph[topic].args:
                            if top.args['title'] + ' = ' + \
                                    topic_graph[topic].args[top.args['title']][hascount[top.args['title']]] + '\n' \
                                    in dB[h + 1].get(0, dB[h + 1].size() - 1):
                                flag = True  # "has" duplicate found
                            dB[h + 1].insert(END, top.args['title'] + ' = '
                                             + topic_graph[topic].args[top.args['title']][
                                                 hascount[top.args['title']]] + '\n')
                        else:
                            printf(topic.title() + ' IS MISSING THE "' + top.args['title'] + '" PROPERTY!')
                    else:
                        dB[h + 1].insert(END, top.args['title'] + '\n')  # Items added to list
                    if flag:
                        dL[h].config(bg="red")
                        dB[h + 1].itemconfig(dB[h + 1].size() - 1, {'bg': 'red'})  # Duplicate marked
                    tempcount += 20  # Tabulates required h change for number of items

                dB[h + 1].place(x=120, y=h, width=290, height=min(200, dB[h + 1].size() * 20))
                dB[h].config(command=dB[h + 1].yview)
                h += min(tempcount, 210)  # Limit h growth to size of scrollbox
                dS[h] = Label(window, text='_' * 410)
                dS[h].place(x=10, y=h, width=410)
                items.append(dS[h])
                h += 20

    window = Tk()
    window.title("Tree Visualization")
    window.geometry("430x860")
    search = Entry(window)
    search.insert(END, 'Search by unique topic key or name (case sensitive)')
    search.place(x=10, y=10, width=350, height=20)
    searchButton = Button(window, text='Search', command=searchClick)
    searchButton.place(x=370, y=10, width=50, height=20)
    leftButton = Button(window, text='<', command=leftClick)
    leftButton.place(x=370, y=40, width=20, height=20)
    rightButton = Button(window, text='>', command=rightClick)
    rightButton.place(x=400, y=40, width=20, height=20)
    webButton = Button(window, text='Web', command=webClick)
    webButton.place(x=330, y=40, width=30, height=20)
    window.bind('<Return>', searchReturn)
    active = {0: 'T1'}
    display('T1') # Show root topic on startup
    window.mainloop()
    return 0 # dupe_test will NOT return until "Tree Visualization" is closed

if __name__ == '__main__':
    dupe_test(GUI=True, exception=False) # Local run