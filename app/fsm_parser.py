import os
import json
from app.robot import TestVoice, CholitaTraction

from transitions import Machine

from app import app, db
from app.models import User, Audio, Program, Action


class Robot(Machine):
    states = []
    transitions = []
    audio_data = {}
    recognition_data = {}
    tts_data = {}
    grammar_data = {}
    trigger_data = {}
    action_data = {}

    def __init__(self, data_dic):
        if data_dic:
            self.states = data_dic['states']
            self.transitions = data_dic['transitions']
            self.audio_data = data_dic['audio_data']
            self.recognition_data = data_dic['recognition_data']
            self.tts_data = data_dic['tts_data']
            self.grammar_data = data_dic['grammar_data']
            self.trigger_data = data_dic['trigger_data']
            self.action_data = data_dic['action_data']

            self.player = TestVoice()
            # available only when deployed in a raspberry pi
            if app.config['RASPI']:
                self.traction = CholitaTraction()

        # init fsm part
            Machine.__init__(self,
                            states=self.states,
                            transitions=self.transitions,
                            initial='init',
                            ignore_invalid_triggers=True)
        else:
            pass

    def isRunning(self):
        return not self.is_oblivion()

    def doThings(self):
        if self.state in self.audio_data:
            filename = Audio.query.filter_by(id=self.audio_data[self.state]).first().filepath
            self.player.play(filename)

        if self.state in self.tts_data:
            phrase = self.tts_data[self.state]
            self.player.speak(phrase)

        if self.state in self.action_data:
            action = Action.query.filter_by(id=self.action_data[self.state]).first()
            if app.config['RASPI']:

                category = action.category
                thingToDo = action.action

                if category == 'traction':
                    self.traction.move(thingToDo)
            else:
                print(action)

    def speak(self):
        # if self.state in self.
        if self.state in self.tts_data.keys():
            phrase = self.tts_data[self.state]
            self.player.speak(phrase)


        self.trigger('end')
        
    def audio(self):
        self.doThings()

        self.trigger('end')



    def presentation(self):
        print('iniciando!')
        self.doThings()

        self.trigger('end')

    def terminate(self):
        self.doThings()

        print('finalizando!')

    def recognition(self):
        print('reconociendo...')
        # check if generic
        if self.state in self.grammar_data:
            # generate grammar
            template_file = os.path.join(app.config['GRAMMARS_FOLDER'], app.config['GRAMMAR_TEMPLATE'])

            with open(template_file, 'r') as f:
                grammar_str = f.read().replace('##commands##', self.grammar_data[self.state])

            # save grammar
            filename = 'auxiliar.gram'
            filepath = os.path.join(app.config['GRAMMARS_FOLDER'], filename)

            # save json file
            with open(filepath, 'w') as out:
                out.write(grammar_str)

            # load grammar
            self.player.loadGrammar('auxiliar')

        # if not generic
        else:
            print("cargando gramatica...")
            self.player.loadGrammar(self.recognition_data[self.state]['grammar'])

        output = self.player.recognize()
        if output:
            print(output)
            if self.state in self.trigger_data:
                self.trigger(self.trigger_data[self.state][output])
            else:
                self.trigger(output)
        else:
            self.trigger('retry')


class JsonFsm(object):
    json_data = {}
    initial = ''
    filepath = ''

    # outputs = []

    def __init__(self):
        # self.trigger('begin')
        self.audio_data = {}
        self.tts_data = {}
        self.recognition_data = {}
        self.grammar_data = {}
        self.trigger_data = {}
        self.states = []
        self.transitions = []
        self.action_data = {}

    def loadFSM(self, filepath):
        print('reiniciando fsm')
        self.filepath = filepath
        self.load()
        return Robot(self.parse())

    def load(self):
        # load entire file
        diagram = {}
        with open(self.filepath, 'r') as f:
            diagram = json.load(f)
        self.json_data = diagram['nodes']

    def parse(self):
        # fill data arrays and dics
        print('parseando')
        st_names = ['s' + n for n in self.json_data.keys()]
        initial = ''
        final = ''

        self.audio_data = {}
        self.tts_data = {}
        self.recognition_data = {}
        self.grammar_data = {}
        self.trigger_data = {}
        self.states = []
        self.transitions = []
        self.action_data = {}

        # states
        for state in st_names:
            callback = self.json_data[state[1:]]['name'].lower()

            if 'presentation' in callback:
                initial = state
                self.checkData(state)

            if 'terminate' in callback:
                final = state
                self.checkData(state)

            # for recognition we must check the type
            if 'recognition' in callback:
                output_str = callback[13:]

                # if recognition generic
                if output_str.isdigit():
                    # get ordered commands
                    rec_comm = []
                    for opt, comm in sorted(self.json_data[state[1:]]['data'].items()):
                        rec_comm.append(comm)

                    # generate and save grammar commands
                    self.grammar_data[state] = " | ".join(rec_comm)
                    self.trigger_data[state] = {value: key for key, value in self.json_data[state[1:]]['data'].items()}

                    self.recognition_data[state] = {'grammar': "generic", 'commands': rec_comm}
                else:

                    rec_comm = self.json_data[state[1:]]['outputs'].keys()
                    self.recognition_data[state] = {'grammar': callback[13:], 'commands': rec_comm}

                callback = 'recognition'

            if 'audio' in callback:
                self.checkData(state)

            if 'speak' in callback:
                c_audio = self.json_data[state[1:]]['data']
                if c_audio:
                    self.tts_data[state] = self.json_data[state[1:]]['data']['text']

            self.states.append({'name': state, 'on_enter': callback})

        # dummy initial state
        self.states.append({'name': 'init'})
        # dummy final state
        self.states.append({'name': 'oblivion'})

        # transitions
        rec_states = []
        for node, data in self.json_data.items():
            for name, out in data['outputs'].items():
                if len(out["connections"]) > 0:
                    self.transitions.append(
                        {
                            'trigger': name,
                            'dest': 's' + str(out["connections"][0]['node']),
                            'source': 's' + node
                        }
                    )
                else:
                    # endpoints
                    self.transitions.append(
                        {
                            'trigger': name,
                            'dest': final,
                            'source': 's' + node
                        }
                    )

            if 'Recognition' in data['name']:
                rec_states.append('s' + node)

        # add self transitionto recognize states
        if rec_states:
            self.transitions.append(
                {
                    'trigger': 'retry',
                    'dest': '=',
                    'source': rec_states
                }
            )
        # add kill transition
        self.transitions.append(
            {
                'trigger': 'kill',
                'dest': 'oblivion',
                'source': '*'
            }
        )

        # dummy initial transition
        self.transitions.append(
            {
                'trigger': 'begin',
                'dest': initial,
                'source': 'init'
            }
        )

        data_dic = {
            'states': self.states,
            'transitions': self.transitions,
            'audio_data': self.audio_data,
            'recognition_data': self.recognition_data,
            'tts_data': self.tts_data,
            'grammar_data': self.grammar_data,
            'trigger_data': self.trigger_data,
            'action_data': self.action_data
        }

        return data_dic

    def checkData(self, state):
        c_audio = self.json_data[state[1:]]['data']
        if c_audio['key'] == 'audio' and 'audio' in c_audio:
            self.audio_data[state] = c_audio['audio']
        if c_audio['key'] == 'text' and 'text' in c_audio:
            self.tts_data[state] = c_audio['text']
        if 'action' in c_audio:
            self.action_data[state] = c_audio['action']
