import rospy
import smach
import random

class FINDGATE(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Gate Found', 'Unable to find'],
                                    input_keys=['distance', 'angle', 'depth'],
                                    output_keys=['return_angle', 'return_distance', 'return_depth'])
        self.gate_attempt = 0
        self.gate_not_found = False
        self.cv = True
        self.detected= None
    
    def execute(self, userdata):
        # get user input on angle, depth, distance
        #if gate not found x1 then turn off CV and turn around same distance
        #if gate not found x2 then fail
        # gate_attempt= 0
        self.detectGate()        

        if(self.detected == False and self.gate_attempt<2):
            self.gate_attempt += 1
            self.turnAround(userdata)
            self.toggleCV()
            rospy.loginfo('Could not find gate. Turning around.')
            rospy.loginfo('Back to origin.')
            rospy.loginfo('Trying again')
            self.turnAround(userdata)
            self.toggleCV()
            self.execute(self, userdata)
            #go back
        if(self.gate_attempt >=2):
            userdata.return_angle = userdata.angle
            userdata.return_distance = userdata.distance
            userdata.return_depth = userdata.depth
            return 'Unable to find'
        if(self.detected):
            userdata.return_angle = userdata.angle
            userdata.return_distance = userdata.distance
            userdata.return_depth = userdata.depth
            return 'Gate Found'

    def toggleCV(self):
        self.cv = not self.cv

    def detectGate(self):
        self.detected = random.randint(0,1) == 1
        #return self.detected

    def turnAround(self,userdata):
        userdata.angle += 180



def main():
    rospy.init_node('gate_machine')
    sm = smach.StateMachine(outcomes=['passed_gate', 'surfaced'])
    sm.userdata.sm_distance = 20
    sm.userdata.sm_angle = 45
    sm.userdata.sm_depth = 10

    with sm:
        smach.StateMachine.add('FINDGATE', FINDGATE(), transitions={
                                                                    'Gate Found': 'PASSGATE',
                                                                    'Unable to find': 'SURFACE'
                                                                    },
                                                        remapping={
                                                                    'distance' : 'sm_distance',
                                                                    'angle':'sm_angle',
                                                                    'depth':'sm_depth'
                                                                    })
        smach.StateMachine.add('PASSGATE', FINDGATE(), transitions={
                                                                    'Gate Passed' : 'passed_gate',
                                                                    'Failed to pass': 'FINDGATE'
                                                                    },
                                                        remapping={
                                                                    'angle': 'sm_angle'
                                                        })
        smach.StateMachine.add('SURFACE', SURFACE(), transitions={
                                                                    'Surfaced': 'surfaced'})


if __name__ == '__main__':
    main()