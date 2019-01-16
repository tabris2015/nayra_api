import json
from robot import TestVoice

from transitions import Machine

from app import app, db
from app.models import User, Audio, Program


class Robot(Machine):
    states = []
    transitions = []
    audio_data = {}
    recognition_data = {}

    def __init__(self, data_dic):
        self.states = data_dic['states']
        self.transitions = data_dic['transitions']
        self.audio_data = data_dic['audio_data']
        self.recognition_data = data_dic['recognition_data']

        self.player = TestVoice()

        # init fsm part
        Machine.__init__(self,
                         states=self.states,
                         transitions=self.transitions,
                         initial='init',
                         ignore_invalid_triggers=True)

    def audio(self):
        if self.state in self.audio_data.keys():
            filename = Audio.query.filter_by(id=self.audio_data[self.state]).first().filepath
            print('reproduciendo {}'.format(filename))
            self.player.play(filename)
        self.trigger('end')

    def presentation(self):
        print('iniciando!')
        if self.state in self.audio_data.keys():
            filename = Audio.query.filter_by(id=self.audio_data[self.state]).first().filepath
            self.player.play(filename)
        self.trigger('end')

    def terminate(self):
        if self.state in self.audio_data.keys():
            filename = Audio.query.filter_by(id=self.audio_data[self.state]).first().filepath
            self.player.play(filename)
        print('finalizando!')

    def recognition(self):
        print('reconociendo...')
        self.player.loadGrammar(self.recognition_data[self.state]['grammar'])
        output = self.player.recognize()
        if output:
            print(output)
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
        pass

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
        st_names = ['s' + n for n in self.json_data.keys()]
        initial = ''
        final = ''

        audio_data = {}
        recognition_data = {}
        states = []
        transitions = []
        # states
        for state in st_names:
            callback = self.json_data[state[1:]]['name'].lower()

            if 'presentation' in callback:
                initial = state
                c_audio = self.json_data[state[1:]]['data']
                if c_audio:
                    audio_data[state] = self.json_data[state[1:]]['data']['audio']

            if 'terminate' in callback:
                final = state
                c_audio = self.json_data[state[1:]]['data']
                if c_audio:
                    audio_data[state] = self.json_data[state[1:]]['data']['audio']

            if 'recognition' in callback:
                rec_comm = self.json_data[state[1:]]['outputs'].keys()
                recognition_data[state] = {'grammar': callback[13:], 'commands': rec_comm}
                callback = 'recognition'

            elif 'audio' in callback:
                c_audio = self.json_data[state[1:]]['data']
                if c_audio:
                    audio_data[state] = self.json_data[state[1:]]['data']['audio']

            states.append({'name': state, 'on_enter': callback})

        # dummy initial state
        states.append({'name': 'init'})
        # dummy final state
        states.append({'name': 'oblivion'})

        # transitions
        rec_states = []
        for node, data in self.json_data.iteritems():
            for name, out in data['outputs'].iteritems():
                if len(out["connections"]) > 0:
                    transitions.append(
                        {
                            'trigger': name,
                            'dest': 's' + str(out["connections"][0]['node']),
                            'source': 's' + node
                        }
                    )
                else:
                    # endpoints
                    transitions.append(
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
            transitions.append(
                {
                    'trigger': 'retry',
                    'dest': '=',
                    'source': rec_states
                }
            )
        # add kill transition
        transitions.append(
            {
                'trigger': 'kill',
                'dest': 'oblivion',
                'source': '*'
            }
        )

        # dummy initial transition
        transitions.append(
            {
                'trigger': 'begin',
                'dest': initial,
                'source': 'init'
            }
        )

        data_dic = {
            'states': states,
            'transitions': transitions,
            'audio_data': audio_data,
            'recognition_data': recognition_data
        }

        return data_dic
