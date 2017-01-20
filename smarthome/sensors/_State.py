from flask_restful import Resource


class State(Resource):

    state = "unkn"
    possible_states = ["home", "out", "bedtime", "sleeping", "party"]

    def get(self):
        return State.state

    def put(self, state):
        if state in self.possible_states:
            State.state = state
