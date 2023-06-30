"""This contains functions to create test-file for whatever i'm currently working on"""


import pymel.core as pm
import serial_animator.animation_io as aio

DATA = None


def create_test_scene_with_data():
    pm.newFile(force=True)
    cube = pm.polyCube(constructionHistory=False)[0]
    cube2 = pm.polyCube(constructionHistory=False)[0]
    pm.setKeyframe(cube2, value=0, time=0, attribute="translateX")
    pm.setKeyframe(cube, value=0, time=0, attribute="translateX")
    pm.setKeyframe(cube, value=20, time=20, attribute="translateX")
    test_layer = pm.animLayer("my_test_layer")
    test_layer2 = pm.animLayer("my_test_layer")
    test_layer.setAttribute(cube.tx)
    test_layer2.setAttribute(cube.tx)
    test_layer.setAttribute(cube.ty)

    pm.setKeyframe(cube, value=1, time=0, attribute="translateX", animLayer=test_layer)
    pm.setKeyframe(cube, value=2, time=10, attribute="translateX", animLayer=test_layer)
    pm.setKeyframe(cube, value=2, time=0, attribute="translateX", animLayer=test_layer2)
    pm.setKeyframe(cube, value=3, time=15, attribute="translateX", animLayer=test_layer2)
    pm.setKeyframe(cube, value=1, time=0, attribute="translateY", animLayer=test_layer)

    global DATA
    DATA = aio.get_anim_data(nodes=[cube])


def new_scene_from_test_data():
    if not DATA:
        create_test_scene_with_data()

    pm.newFile(force=True)
    cube, = pm.polyCube(constructionHistory=False)

    test_layer = pm.animLayer("my_test_layer")
    test_layer.setAttribute(cube.tx)
    pm.setKeyframe(cube, value=1, time=0, attribute="translateX", animLayer=test_layer)
    node_dict = {cube.fullPath(): cube}
    aio.set_anim_data(DATA, node_dict)
