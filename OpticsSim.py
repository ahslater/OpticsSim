# -*- coding: UTF-8 -*-
#Imports
import math

import pygame
from pygame.locals import *

PI = math.pi

# Common Colours
BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
DARKGREEN = (30,135,27)
BLUE = (0,0,255)
LIGHTBLUE = (135,206,250)
MEDIUMBLUE = (0,123,166)
DARKBLUE = (24,76,160)
LIGHTGREY = (220,220,220)
MEDIUMGREY = (130,130,130)


class Button:

    '''Generic button for selecting an option'''

    def __init__(self, x, y, text, fontname, fontcolor, fillcolor, bordercolor):
        self.fillrect = pygame.Rect(x,y,0,0) # Width and height adjusted when text is rendered
        self.bordrect = pygame.Rect(x,y,0,0)
        self.text = text
        self.pressed = False
        self.fontname = fontname
        self.fontcolor = fontcolor
        self.fillcolor = fillcolor
        self.bordcolor = bordercolor

    def handle_event(self, event):
        # Check if clicked on
        if event.type == MOUSEBUTTONDOWN:
           if self.fillrect.collidepoint(event.pos):
               self.pressed = True

    def draw(self, screen, alignment, coords, assets):
        #Update position based on given coordinates
        exec("self.fillrect.{0} = self.bordrect.{0} = {1}".format(alignment,coords))
        #Fill
        pygame.draw.rect(screen, self.fillcolor, self.fillrect)
        #Border
        pygame.draw.rect(screen, self.bordcolor, self.bordrect,2)
        #Text
        text = assets[self.fontname].render(self.text,True,self.fontcolor)
        textRect = text.get_rect(topleft=(self.fillrect.topleft[0]+3,self.fillrect.topleft[1]+3))
        screen.blit(text,textRect)

        #Adjust fill and border to the size of the text
        self.fillrect.w = self.bordrect.w = textRect.w + 5
        self.fillrect.h = self.bordrect.h = textRect.h + 5

class BaseScene:

    '''The base class for all scenes of the program'''

    # Common methods to all scenes
    def __init__(self):
        # Stay on same scene by default
        self.next = self

    def SwitchToScene(self, next_scene):
        ''' Move to scene at the end of the loop'''
        self.next = next_scene()

    def Terminate(self):
        ''' Close the program at the end of the loop'''
        self.next = None

    def DrawBanner(self, screen, assets):
        ''' Draw title banner at the top of the screen'''
        # White background, blue banner
        screen.fill(WHITE)
        pygame.draw.rect(screen,MEDIUMBLUE,(0,0,screen.get_width(),45),0)

        # Title
        titleText = assets['largeFont'].render(self.title,True,WHITE)
        titleTextRect = titleText.get_rect(midtop=(screen.get_width()/2, 2))
        screen.blit(titleText,titleTextRect)

    # Methods to be overridden
    def ProcessInput(self, events):
        ''' Update class attributes based on input'''
        raise NotImplementedError

    def Render(self, screen, assets):
        ''' Draws graphics to "screen" surface that is updated at the end of each loop'''
        raise NotImplementedError

## Objects for simulator
class Laser:

    '''Object for simulator. Includes emission of laser particle that draws beam'''

    def __init__(self, center, rot=0, decayincr=0.5, on=True):

        self.center = center
        # w=38 and h=72 generally appropriate on most monitors
        self.width = 38
        self.height = 72
        # Rotation given in degrees, math module works in radians
        self.rotdeg = rot
        self.rotrads = math.radians(rot)

        # Load pointer image and transform to correct position
        temp_image = pygame.image.load("laser.png")
        temp_image = pygame.transform.smoothscale(temp_image, (self.width, self.height))
        self.image = pygame.transform.rotate(temp_image, rot)
        self.rect = self.image.get_rect(center=center)

        # On or off
        self.on = on
        # Decay light path (to white). Bigger number means quicker decay
        self.decayincr = decayincr

    def draw(self, screen):
        # Draw pointer
        screen.blit(self.image, self.rect)

    def emit_particle(self, screen, mirrors, blocks):
        ''' Draws laser path by emitting particle that interacts with given mirrors and blocks'''

        # Check that it should be emitting
        if self.on == False:
            return

        # Set particle to correct position based on pointer
        x,y = self.rect.center
        x -= self.height*math.sin(self.rotrads)/2
        y -= self.height*math.cos(self.rotrads)/2
        partRect = pygame.Rect(x,y,3,3)
        partRect.center = (x,y)

        # Set initial direction
        currangle = self.rotrads
        # Small multiplier increases accuracy of collision points but slows down rendering
        velMultiplier = 0.5
        xvel = - math.sin(self.rotrads) * velMultiplier
        yvel = - math.cos(self.rotrads) * velMultiplier

        # Starts in air so refractive index of 1
        currn = 1

        # Intensity decays as it goes
        intensity = 0

        while 0 < x < screen.get_width() and 0 < y < screen.get_height():

            for mirror in mirrors:
                if mirror.line.dist((x,y)) <= 0.5 * velMultiplier:

                    spinangle = 2 * PI - currangle

                    #Relative position of point1 on line
                    linerelx1 = mirror.line.x1 - x
                    linerely1 = y - mirror.line.y1
                    #Rotate for particle's perspective
                    spunx1 = math.cos(spinangle)*linerelx1 - math.sin(spinangle)*linerely1
                    spuny1 = math.sin(spinangle)*linerelx1 + math.cos(spinangle)*linerely1

                    #Relative position of point2 on line
                    linerelx2 = mirror.line.x2 - x
                    linerely2 = y - mirror.line.y2
                    #Rotate for particle's perspective
                    spunx2 = math.cos(spinangle)*linerelx2 - math.sin(spinangle)*linerely2
                    spuny2 = math.sin(spinangle)*linerelx2 + math.cos(spinangle)*linerely2

                    #Only consider point to the left of collision
                    if spunx1 < 0:
                        spunx = spunx1
                        spuny = spuny1
                    elif spunx2 < 0:
                        spunx = spunx2
                        spuny = spuny2
                    else:
                        # Particle direction near parallel to mirror line
                        # To avoid program crash, let go in straight line
                        continue

                    #Calc theta1
                    if spuny == 0:
                        # Head on collision
                        theta1 = 0
                    else:
                        theta1 = math.atan(spuny/spunx)

                    # Amount that the particle direction turns to the "right"
                    newrelangle = PI - 2 * theta1
                    # Set to new direction
                    currangle -= newrelangle
                    # Make sure 0 <= angle < 2pi
                    currangle %= 2 * PI
                    # Set new velocities
                    xvel = - math.sin(currangle) * velMultiplier
                    yvel = - math.cos(currangle) * velMultiplier

            for block in blocks:
                for line in block.lines:
                    if line.dist((x,y)) < 0.5 * velMultiplier:

                        # Passing through wall of block so refracting
                        if block.n == currn:
                            # Going out
                            newn = 1
                        else:
                            # Going in
                            newn = block.n

                        spinangle = 2 * PI - currangle

                        #Relative position of point1 on line
                        linerelx1 = line.x1 - x
                        linerely1 = y - line.y1
                        #Rotate for particle's perspective
                        spunx1 = math.cos(spinangle)*linerelx1 - math.sin(spinangle)*linerely1
                        spuny1 = math.sin(spinangle)*linerelx1 + math.cos(spinangle)*linerely1

                        #Relative position of point2 on line
                        linerelx2 = line.x2 - x
                        linerely2 = y - line.y2
                        #Rotate for particle's perspective
                        spunx2 = math.cos(spinangle)*linerelx2 - math.sin(spinangle)*linerely2
                        spuny2 = math.sin(spinangle)*linerelx2 + math.cos(spinangle)*linerely2

                        #Only consider point to the left of collision
                        if spunx1 < 0:
                            spunx = spunx1
                            spuny = spuny1
                        elif spunx2 < 0:
                            spunx = spunx2
                            spuny = spuny2
                        else:
                            # Particle direction near parallel to line
                            # Can travel along boundary, let go in straight line
                            continue

                        if spuny ==0:
                            theta1=0
                        else:
                            theta1 = abs(math.atan(spuny/spunx))

                        # Check for total internal reflection
                        if newn < currn and theta1 > abs(math.asin(newn/currn)):
                            # Contine with same code as mirror
                            # Amount that the particle direction turns to the "right"
                            if spuny <= 0:
                                newrelangle =  PI - 2 * theta1
                            else:
                                newrelangle =  -PI + 2 * theta1
                            # Staying in block so set newn back to currn
                            newn = currn
                        else:
                            # Normal refraction
                            theta2 = math.asin(currn * math.sin(theta1) / newn)
                            if spuny <= 0:
                                newrelangle = -theta1 + theta2
                            else:
                                newrelangle = theta1 - theta2

                        # Set to new direction and refractive index (n)
                        currangle -= newrelangle
                        currn = newn
                        # Make sure 0 <= angle < 2pi
                        currangle %= 2 * PI
                        # Set new velocities
                        xvel = - math.sin(currangle) * velMultiplier
                        yvel = - math.cos(currangle) * velMultiplier

                        x += 2*xvel
                        y += 2*yvel

            #Update position
            x += xvel
            y += yvel
            partRect.center = (x,y)

            # Decay intensity and update colour
            intensity += self.decayincr
            # Threshold for now white and stop rendering path
            if intensity > 250:
                break
            colour = (255,intensity,intensity)

            pygame.draw.rect(screen, colour, partRect)

class Line:

    ''' Helper class for Block and Mirror with information to help find distance to a point for collision detection.'''

    def __init__(self, point1, point2):

        # Define points so they are easy to reference
        self.point1 = point1
        self.point2 = point2
        self.x1, self.y1 = point1
        self.x2, self.y2 = point2

        # Change in x and y along the line
        self.linedx = self.x2 - self.x1
        self.linedy = self.y2 - self.y1

        # Used in formula
        self.r = self.linedx ** 2 + self.linedy ** 2

    def dist(self, point):
        '''Calculate and return distance from point to line'''
        # Coordinates of point to find distance to
        xp, yp = point

        # Ratio of how far along the line the closest point on the line to the given point is
        u =  ((xp - self.x1) * self.linedx + (yp - self.y1) * self.linedy) / self.r

        if u > 1:
            # Beyond the line so closest to x2,y2
            u = 1
        elif u < 0:
            # Before the line so closest to x1,y1
            u = 0

        # Closest point on line to given point
        xclosest = self.x1 + u * self.linedx
        yclosest = self.y1 + u * self.linedy

        # Using pythagoras' theorem
        dx = xclosest - xp
        dy = yclosest - yp
        distance = math.sqrt(dx**2 + dy**2)

        return distance

class Mirror:

    ''' Object for simulator. Acts like a double sided mirror'''

    def __init__(self, pos1, pos2):
        self.x1, self.y1 = pos1
        self.x2, self.y2 = pos2
        self.pos1 = pos1
        self.pos2 = pos2
        self.line = Line(pos1, pos2)

    def draw(self, screen):
        # Only thing to draw is one line
        pygame.draw.line(screen, DARKGREEN, self.pos1, self.pos2, 5)

class Block:

    ''' Object for simulator. A block with a different refractive index to air.'''

    def __init__(self,points,n):
        # Corners of shape
        self.points = points
        # Refractive index of block
        self.n = n

        # Create list of lines connecting the points
        self.lines = []
        for i1 in range(len(points)):
            i2 = i1 + 1
            if i2 == len(points):
                i2 = 0
            self.lines.append( Line( points[i1], points[i2] ) )

    def draw(self,screen):
        # Solid fill and visible border
        pygame.draw.polygon(screen, LIGHTGREY, self.points)
        pygame.draw.lines(screen, MEDIUMGREY, True, self.points, 1)

class SemiCircleBlock(Block):

    ''' Object for simulator. A semi-circular block.'''

    def __init__(self,center,radius,rotation,n):
        self.center = center
        self.x, self.y = center
        # When adding as an object, radius could be zero causing a div/0 error. Approximate with 1
        if radius == 0:
            radius = 1
        self.radius = radius

        self.n = n # Refracive index
        self.rot = rotation # Clockwise from north in radians

        # Create a set of points to approximate curve of semicircle
        self.points = []
        self.points.append((self.x - radius * math.sin(rotation), self.y + radius * math.cos(rotation))) #Corner 1
        self.points.append((self.x + radius * math.sin(rotation), self.y - radius * math.cos(rotation))) #Corner 2

        # Increment angle by small steps to approximate points that would lie on curve
        angle = rotation + 0.1
        while angle < rotation + PI:
            # Points for curve
            self.points.append((self.x + radius * math.sin(angle), self.y - radius * math.cos(angle)))
            angle += 0.1

        # Create list of lines, curve is represented by many lines
        self.lines = []
        for i1 in range(len(self.points)):
            i2 = i1 + 1
            if i2 == len(self.points):
                i2 = 0
            self.lines.append(Line(self.points[i1], self.points[i2]))

class SimulatorScene(BaseScene):

    '''Where the user can experiment with the simulation'''

    def __init__(self):
        BaseScene.__init__(self)
        self.title = "Simulator"

        # Lists of current objects
        self.lasers = []
        self.mirrors = []
        self.blocks = []

        # Buttons to add objects
        self.laserbut = Button(0,0,"Laser","smallFont",BLACK,WHITE,BLACK)
        self.mirrorbut = Button(0,0,"Mirror","smallFont",BLACK,WHITE,BLACK)
        self.blockbut = Button(0,0,"Block","smallFont",BLACK,WHITE,BLACK)
        self.semicirclebut = Button(0,0,"Semicircular Block","smallFont",BLACK,WHITE,BLACK)

        # Button to reset the screen
        self.resetbut = Button(0,0,"Reset","mediumFont",DARKBLUE,WHITE,BLACK)

        # The "neutral" state where no objects are being added, state tells the user what they should be selecting
        self.state = "an object"

    def ProcessInput(self, events):
        for event in events:
            # Buttons check if they have been clicked
            self.resetbut.handle_event(event)
            self.laserbut.handle_event(event)
            self.mirrorbut.handle_event(event)
            self.blockbut.handle_event(event)
            self.semicirclebut.handle_event(event)

            if event.type == MOUSEBUTTONDOWN:
                # Neutral state is "an object" where everything is fixed on screen
                # and it is waiting for a button to be pressed

                mouse = pygame.mouse.get_pos()

                # First click for laser sets centre position
                if self.state == "Laser Centre":
                        self.lasers.append(Laser(mouse,decayincr=1))
                        self.state = "Laser Direction"

                # Second click for laser sets where to point towards
                elif "Laser Direction" in self.state:
                    # Set final laser to a long time to decay (small decay increment)
                    self.lasers[-1] = Laser(self.lasers[-1].center, rot=self.lasers[-1].rotdeg, decayincr = 0.01)
                    # Laser position is final go back to neutral state
                    self.state = "an object"

                # First click for mirror create Mirror object at the point they clicked
                elif self.state == "Mirror Point 1":
                    # mouse x and y are incremented by one so that the length of the mirror is non-zero
                    self.mirrors.append(Mirror(mouse,(mouse[0]+1,mouse[1]+1)))
                    self.state = "Mirror Point 2"

                # Second click for mirror sets final position
                elif self.state == "Mirror Point 2":
                    # Mirror already updated and rendered, go back to neutral state
                    self.state = "an object"

                # First click for block starts building currblock
                # Nothing to render so nothing added to Blocks list
                elif self.state == "Block Point 1":
                    self.currblock = [mouse]
                    self.state = "Block Point 2"

                # Second click for block sets another point
                elif self.state == "Block Point 2":
                    if mouse not in self.currblock:
                        self.currblock.append(mouse)
                        self.state = "Block Point 3"

                # Third click for block now makes polygon so added to list
                elif self.state == "Block Point 3":
                    if mouse not in self.currblock:
                        self.currblock.append(mouse)
                        self.blocks.append(Block(self.currblock,1.52))
                        self.state = "More Block Points, Right-click to stop"

                # Any more than the third click, either allows more points to
                # be defined or a right click returns the state to neutral
                elif self.state == "More Block Points, Right-click to stop":
                    if event.button == 3: #Right Click
                        self.state = "an object"
                    else:
                        if mouse not in self.currblock:
                            self.currblock.append(mouse)
                            self.blocks[-1] = Block(self.currblock,1.52)

                # First click for semicircle defines centre
                elif self.state == "Semicircle Centre":
                    self.blocks.append(SemiCircleBlock(mouse, 1, 0, 1.52))
                    self.state = "Semicircle Orientation"

                # Second click for semicircle defines orientation
                elif "Semicircle Orientation" in self.state:
                    # Semicircle block position is final, go back to neutral state
                    self.state = "an object"

    def Update(self):
        # Reset simulator by starting new scene if button pressed
        if self.resetbut.pressed == True:
            self.SwitchToScene(SimulatorScene)

        # Buttons to start procedure to add each object
        if self.laserbut.pressed == True:
            self.state = "Laser Centre"
            self.laserbut.pressed = False

        if self.mirrorbut.pressed == True:
            self.state = "Mirror Point 1"
            self.mirrorbut.pressed = False

        if self.blockbut.pressed == True:
            self.state = "Block Point 1"
            self.blockbut.pressed = False

        if self.semicirclebut.pressed == True:
            self.state = "Semicircle Centre"
            self.semicirclebut.pressed = False

        # "Live" responding object creation code is here

        # Second click for laser sets where to point towards
        if "Laser Direction" in self.state:
            cen = self.lasers[-1].center
            mouse = pygame.mouse.get_pos()

            # Set angle to point towards mouse
            dx = mouse[0] - cen[0]
            dy = mouse[1] - cen[1]
            angle = math.degrees(math.atan2(-dy,dx)) - 90
            angle %= 360

            # Show angle on screen
            self.state = "Laser Direction " + str(round(360-angle,1)) + "°"

            # Replace last laser to now point in new direction
            self.lasers[-1] = Laser(self.lasers[-1].center, rot=angle, decayincr=1)

        # Second click for mirror is "live"
        elif self.state == "Mirror Point 2":
            point1 = self.mirrors[-1].pos1
            mouse = pygame.mouse.get_pos()
            if mouse == point1:
                mouse = (mouse[0]+1,mouse[1]+1)
            # Replace last mirror to join to the position of the mouse
            self.mirrors[-1] = Mirror(point1,mouse)

        # Second semicircle click is "live" orientation
        elif "Semicircle Orientation" in self.state:
            # Code is similar to laser direction as also setting direction
            cen = self.blocks[-1].center
            mouse = pygame.mouse.get_pos()

            dx = mouse[0] - cen[0]
            dy = mouse[1] - cen[1]

            # New radius
            radius = math.sqrt(dx**2 + dy**2)

            # Set angle to point towards mouse
            angle = PI/2 - math.atan2(-dy,dx)
            angle %= 2*PI

            # Show angle on screen
            self.state = "Semicircle Orientation " + str(round(math.degrees(angle),1)) + "°"

            # Replace last laser to now point in new direction
            self.blocks[-1] = SemiCircleBlock(cen, radius, angle, 1.52)

    def Render(self, screen, assets):
        self.DrawBanner(screen, assets)

        # Buttons
        self.laserbut.draw(screen, "bottomleft", (5, screen.get_height()-5), assets)
        self.mirrorbut.draw(screen, "bottomleft", (70, screen.get_height()-5), assets)
        self.blockbut.draw(screen, "bottomleft", (135, screen.get_height()-5), assets)
        self.semicirclebut.draw(screen, "bottomleft", (195, screen.get_height()-5), assets)
        self.resetbut.draw(screen, "topleft", (5,3), assets)

        # Instructions
        instText = assets['smallFont'].render("Click to select "+self.state,True,BLACK)
        instTextRect = instText.get_rect(bottomleft = (375, screen.get_height()-5))
        screen.blit(instText,instTextRect)

        # Objects
        for block in self.blocks:
            block.draw(screen)
        for mirror in self.mirrors:
            mirror.draw(screen)
        for laser in self.lasers:
            laser.draw(screen)
            laser.emit_particle(screen,self.mirrors,self.blocks)

def main(width, height, fps):
    # Initialisation
    pygame.init()
    pygame.display.set_caption('Optics Simulation')
    screen = pygame.display.set_mode((width, height),DOUBLEBUF|RESIZABLE)
    clock = pygame.time.Clock()

    # Fonts used across the scenes
    assets = {
        'smallFont' : pygame.font.SysFont('arial', 20),
        'mediumFont' : pygame.font.SysFont('arial', 25),
        'largeFont' : pygame.font.SysFont('arial', 35)
        }

    # Set scene to the simulator
    active_scene = SimulatorScene()

    # Main Loop
    while active_scene != None:

        # Event handling
        events = pygame.event.get()
        for event in events:
            # Allow the window to be any size
            if event.type == VIDEORESIZE:
                screen=pygame.display.set_mode(event.dict['size'],HWSURFACE|DOUBLEBUF|RESIZABLE)
            # Close the program
            elif event.type == pygame.QUIT:
                active_scene.Terminate()

        active_scene.ProcessInput(events)
        active_scene.Update()
        active_scene.Render(screen,assets)

        active_scene = active_scene.next

        pygame.display.update()
        clock.tick(fps)

    # Quit program
    pygame.quit()

# Allow classes to be used by other programs in future development so only execute if main
if __name__ == "__main__":
    main(700,600,30)
