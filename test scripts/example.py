import time
import numpy as np

"""
Progress Bar!
+ for more information: https://stackoverflow.com/a/34325723
"""


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd='\n'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "", "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    # print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=printEnd)  # how it should work in a normal shell
    print('%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def main():
    """
    Here's a terrible bug that took some time to resolve:

    The textual progress bar had been working all day... Except at some point it somehow ceased to. Very odd and very
    frustrating. I scoured the MainLauncher.py GUI and the progress_bary.py trying to see what might have caused the issue.

    What was the issue specifically?
    When I would run progress_bary.py script within the MainLauncher.py GUI, the progress bar would no longer display inside
    the text ctrl object correctly. Yet, I would see faint updates as the text approached the bottom of the control
    object when the object was forced to start scrolling with the new text updates to the object. To make matters worse,
    whenever I would move the cursor around the interface, the text updates being fed into the text ctrl object would
    sometimes skip, kludge two lines together, or simply break the subprocess!

    Possible reasons
    I felt lost trying to understand what could have happened. I recalled being careful not too change or delete
    anything without at least re-running the GUI first. Yet here we were with a terrible bug. I at least had a few
    clues:
        > Moving the cursor now affected the text ctrl box for the first time. Strange. This led me to suspect there was
          an issue with the wx.CallAfter call in the MainLauncher.py gui script. Yet, upon careful inspection, nothing seemed
          out of place. Was it perhaps the arrangement of the CallAfter queuing? No change in this regard improved the
          outcome. So, while I suspected my cursor was now interrupting the CallAfter queuing of the GUI frame, no
          changes to likely suspects affected the outcome.

        >  example.py may be the perpetrator in all of this... To investigate this, I stripped back all the work
           that had be done to produce true data for the gui to process. In the end, the loop was reverted to printing
           what index of the sequence the for loop was on. No change. Wow! Now I was starting to get worried.

        [SOLUTION] - what was the solution, then? The placement of the time.sleep function call in the script. Before,
                     it had been placed at the beginning of the for loop to simulate processing time. Later on, I had
                     inevitably moved it to the end of the loop to improve readability of the new features I had
                     implemented. This inherently wasn't an issue. HOWEVER, I did not place it at the very end of the
                     loop. I placed it BETWEEN the 'print' and 'printProgressBar' calls. At a glance, I originally
                     though this was a sufficient place to insert a delay into the loop. Placing a delay after the first
                     write before the second write seemed like a sound approach to ensuring there was no unintentional
                     endiannes. In other words, a delay between two calls to wx.CallAfter seemed just fine. In this
                     instance; however, this was not the case. To correct the mistake, call to time.sleep is ensured to
                     occur before or after ALL features of the loop pertaining to wx.CallAfter have executed.

        [THE LESSON LEARNED] - what was the lesson learned here? I really need to invest in a git repository to log my
                               changes from now on... Fortunately, I was saved by PyCharm's 'Local History' found under
                               VCS > Local History > Show History. Here I was able to wind back the clock quite a bit to
                               see what in fact really did change from just this morning to later that afternoon.

    """
    print('Beginning test!')
    # Make a mesh in the space of parameterisation variables u and v
    u = None
    v = None
    """
    Geometric Shapes
    https://github.com/index-0/Geometric-Shapes
    """
    selection = 'example'
    if selection == 'example':
        n_radii = 8
        n_angles = 36

        # Make radii and angles spaces (radius r=0 omitted to eliminate duplication).
        radii = np.linspace(0.125, 1.0, n_radii)
        angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)

        # Repeat all angles for each radius.
        angles = np.repeat(angles[..., np.newaxis], n_radii, axis=1)

        # Convert polar (radii, angles) coords to cartesian (x, y) coords.
        # (0, 0) is manually added at this stage,  so there will be no duplicate
        # points in the (x, y) plane.
        x = np.append(0, (radii * np.cos(angles)).flatten())
        y = np.append(0, (radii * np.sin(angles)).flatten())

        # Compute z to make the pringle surface.
        z = np.sin(-x * y)

    elif selection == 'mobius':
        u = np.linspace(0, 2.0 * np.pi, endpoint=True, num=50)
        v = np.linspace(-0.5, 0.5, endpoint=True, num=10)
        u, v = np.meshgrid(u, v)
        u, v = u.flatten(), v.flatten()
        x = (1 + 0.5 * v * np.cos(u / 2.0)) * np.cos(u)
        y = (1 + 0.5 * v * np.cos(u / 2.0)) * np.sin(u)
        z = 0.5 * v * np.sin(u / 2.0)

    elif selection == 'torus':
        u = np.linspace(0, 2 * np.pi, endpoint=True, num=30)
        v = np.linspace(0, 2 * np.pi, endpoint=True, num=30)
        u, v = np.meshgrid(u, v)
        u, v = u.flatten(), v.flatten()
        R = float(input("Insert R (major radius): "))
        r = float(input("Insert r (minor radius): "))
        x = np.cos(v) * (R + r * np.cos(u))
        y = np.sin(v) * (R + r * np.cos(u))
        z = r * np.sin(u)

    items = len(x)
    data = [[int(0)] * 6] * items

    # Initial call to print 0% progress
    printProgressBar(0, items, prefix='Progress:', suffix='Complete', length=39)
    for i in range(items):
        t = i * 0.0005
        data[i][0] = i
        data[i][1] = t
        data[i][2] = np.sin(100 * t) * np.sin(1000 * t)

        data[i][3] = x[i]
        data[i][4] = y[i]
        data[i][5] = z[i]

        print(f'[TABLE] {data[i]}')

        # Update Progress Bar
        printProgressBar(i + 1, items, prefix='Progress:', suffix='Complete', length=39)

        time.sleep(0.1)

    print('finished progress bar!')


if __name__ == '__main__':
    main()
