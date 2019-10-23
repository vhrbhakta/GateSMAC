import rospy
import smach
import random
import sys
'''
 Make Github for main RoboSub add Mark to it
 connect Travis CI to the Github
 Start making unit tests in Python for edge cases -> Add those unit tests to the Travis CI .yaml file
'''

class FINDGATE(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Gate Found', 'Unable to find','Failed'],
                                    input_keys=['cv','distance', 'angle', 'depth'],
                                    output_keys=['return_cv'])
        self.gate_attempt = 0
        self.gate_not_found = True
        self.cv = True
        self.detected= False
        
    
    def execute(self, userdata):
        # get user input on angle, depth, distance
        #if gate not found x1 then turn off CV and turn around same distance
        #if gate not found x2 then fail
        # rospy.loginfo(userdata.depth)

        self.distance_traveled=0
        while(self.distance_traveled <userdata.distance):
            self.detectGate()
            self.distance_traveled+= 1
               

        if(self.detected == False and self.gate_attempt<2):
            self.gate_attempt += 1
            # self.turnAround(userdata)
            # self.toggleCV()
            
            # self.turnAround(userdata)
            # self.toggleCV()
            # self.execute(self, userdata)
            
            userdata.return_cv = self.cv
            rospy.loginfo('Could not find gate. Turning around.')
            return 'Unable to find'
            #go back
        if(self.gate_attempt >=2):
            return 'Failed'

        if(self.detected):
            return 'Gate Found'

    # def toggleCV(self):
    #     self.cv = not self.cv

    def detectGate(self):
        self.detected = random.randint(0,1) == 1
        #return self.detected

    # def turnAround(self,userdata):
    #     userdata.angle += 180

class RETRYFIND(smach.State):
    def __init__(self):
         smach.State.__init__(self, outcomes=['back to origin'],
                                    input_keys=['cv','distance', 'angle', 'depth'],
                                    output_keys=['return_cv', 'return_depth'])
    
    def execute(self, userdata):
        # rospy.loginfo(userdata.depth)
        self.angle = userdata.angle
        userdata.return_cv = False
        self.angle += 180
        userdata.return_depth = userdata.depth -2
        
        self.dist = userdata.distance
        
        while(self.dist >0):
            self.dist -= 1

        rospy.loginfo('Trying again')
        rospy.loginfo('Back to origin.')
        
        userdata.return_cv = True
        return 'back to origin'


class PASSGATE(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Gate Passed', 'Failed to pass'],
                                input_keys=['cv'],
                                output_keys=['return_cv'])
        self.centered = False
        self.pass_distance = 10

    def execute(self, userdata):
        # rospy.loginfo(userdata.cv)

        if(not userdata.cv):
            userdata.return_cv = True

        self.centered = self.centerGate()
        if(self.centered):
            while(self.pass_distance>0):
                self.pass_distance -= 1
            self.pass_distance = 10
            return 'Gate Passed'
        else:
            return 'Failed to pass'

    def centerGate(self):
        return (random.randint(0,1) == 1)

class SURFACE(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Surfaced'],
                                    input_keys=['depth'])
        
    def execute(self, userdata):
        rospy.loginfo(userdata.depth)
        self.depth = userdata.depth
        while(self.depth >0):
            self.depth -= 1
        return 'Surfaced'

def main():
    rospy.init_node('gate_machine')
    sm = smach.StateMachine(outcomes=['passed_gate', 'surfaced'])

    arguments = len(sys.argv) -1
    if(arguments != 4):
        print("Incorrect number of arguements.\nUse: gateMachine.py [dist] [angle] [depth] [CV]")
        exit(1)
    
    parameter = 1
    while(parameter <=arguments-1):
        if(not sys.argv[parameter].isdigit()):
            print("Invalid input. Please enter numbers.")
            exit(1)
        parameter=parameter +1
        
        
    if((sys.argv[4] != "True") or (not sys.argv[4] != "False")):
        print("Invalid input. 4th arg, [CV], must be boolean")
        exit(1)
    
    sm.userdata.sm_cv = True

    if(sys.argv[4] == "True"):
        sm.userdata.sm_cv = True
    else:
        sm.userdata.sm_cv=False
    
    sm.userdata.sm_distance = int(sys.argv[1])
    sm.userdata.sm_angle = int(sys.argv[2])
    sm.userdata.sm_depth = int(sys.argv[3])
    

    # sm.userdata.sm_distance = 20
    # sm.userdata.sm_angle = 45
    # sm.userdata.sm_depth = 10
    # sm.userdata.sm_cv = True

    with sm:
        #find gate using CV
        smach.StateMachine.add('FINDGATE', FINDGATE(), transitions={
                                                                    'Gate Found': 'PASSGATE',
                                                                    'Unable to find': 'RETRYFIND',
                                                                    'Failed':'SURFACE'
                                                                    },
                                                        remapping={
                                                                    'cv' : 'sm_cv',
                                                                    'distance' : 'sm_distance',
                                                                    'angle':'sm_angle',
                                                                    'depth':'sm_depth',
                                                                    
                                                                    'return_cv': 'sm_cv'
                                                                    })
        #go 2 ft up, turn CV off, and turn around and go forward given distance to go back to 'origin'
        smach.StateMachine.add('RETRYFIND', RETRYFIND(), transitions={
                                                                    'back to origin':'FINDGATE'
                                                                    },
                                                        remapping = {
                                                                    'distance' : 'sm_distance',
                                                                    'angle':'sm_angle',
                                                                    'depth':'sm_depth',
                                                                    'cv':'sm_cv',
                                                                    'return_depth':'sm_depth',
                                                                    'return_cv':'sm_cv'})
        #center the gate within CV bounding box and go forward
        smach.StateMachine.add('PASSGATE', PASSGATE(), transitions={
                                                                    'Gate Passed' : 'passed_gate',
                                                                    'Failed to pass': 'RETRYFIND'
                                                                    },
                                                        remapping={
                                                                    'cv': 'sm_cv',
                                                                    'return_cv':'sm_cv'
                                                        })
        #make depth = 0
        smach.StateMachine.add('SURFACE', SURFACE(), transitions={
                                                                    'Surfaced': 'surfaced'},
                                                    remapping={
                                                                    'depth':'sm_depth'
                                                    })


    outcome = sm.execute()


if __name__ == '__main__':
    main()