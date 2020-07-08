from opentrons import protocol_api
import json
import os
import math

# metadata
metadata = {
    'protocolName': 'V1 Station A LAL P300',
    'author': 'Ricmag <ricmags@sapo.pt>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}

NUM_SAMPLES = 10
SAMPLE_VOLUME = 100
TIP_TRACK = False


def run(ctx: protocol_api.ProtocolContext):

    # load labware
    #ic_pk = ctx.load_labware(
     #   'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '1',
      #  'chilled tubeblock for internal control and proteinase K (strip 1)').wells()[0]
    source_racks = [
        ctx.load_labware(
            'opentrons_15_tuberack_falcon_15ml_conical', slot,
            'source tuberack ' + str(i+1))
        for i, slot in enumerate(['11', '10', '7', '4', '5', '6', '3'])
    ]
    dest_plate = ctx.load_labware(
        'nest_96_wellplate_200ul_flat', '9', '96-wellplate sample plate')
    #binding_buffer = ctx.load_labware(
    #   'opentrons_6_tuberack_falcon_50ml_conical', '7',
    #  '50ml tuberack for binding buffer (tubes A1+B1)').wells()[:1]
    # binding_buffer = ctx.load_labware(
    #     'biorad_96_wellplate_200ul_pcr', '7',
    #     '50ml tuberack for lysis buffer + PK (tube A1)').wells()[:1]
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '8')]
   # tipracks20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', '10',
   #                                '20µl filter tiprack')]

    # load pipette
    #m20 = ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=tipracks20)
    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)


    # setup samples
    sources = [
        well for rack in source_racks for well in rack.wells()][:NUM_SAMPLES]
    dests_single = dest_plate.wells()[:NUM_SAMPLES]
    num_cols = math.ceil(NUM_SAMPLES/8)
    dests_multi = dest_plate.rows()[0][:num_cols]

    tip_log = {'count': {}}
    folder_path = '/data/A'
    tip_file_path = folder_path + '/tip_log.json'
    if TIP_TRACK and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips300' in data:
                    tip_log['count'][p300] = data['tips300']
                else:
                    tip_log['count'][p300] = 0
    #            if 'tips20' in data:
    #                tip_log['count'][m20] = data['tips20']
    #            else:
    #                tip_log['count'][m20] = 0
    else:
        tip_log['count'] = {p300: 0}#, m20: 0}

    tip_log['tips'] = {
        p300: [tip for rack in tips300 for tip in rack.wells()],
    #    m20: [tip for rack in tipracks20 for tip in rack.rows()[0]]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [p300]#, m20]
    }

    def pick_up(pip):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip]:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
        tip_log['count'][pip] += 1

    #heights = {tube: 20 for tube in binding_buffer}
   # radius = (binding_buffer[0].diameter)/2
   # min_h = 5
#
   # def h_track(vol, tube):
   #     nonlocal heights
   #     dh = vol/(math.pi*(radius**2))
  #      if heights[tube] - dh > min_h:
   #         heights[tube] = heights[tube] - dh
   #     else:
   #         heights[tube] = min_h  # stop 5mm short of the bottom
   #     return heights[tube]

    # transfer sample
    for s, d in zip(sources, dests_single):
        pick_up(p300)
        for _ in range(1):
            p300.aspirate (250, s.bottom(5))
            p300.dispense (250, s.bottom(5))
        p300.transfer(SAMPLE_VOLUME, s.bottom(5), d.bottom(5), air_gap=20,
                       new_tip='never')
        p300.air_gap(20)
        p300.drop_tip()

    # transfer binding buffer and mix
    #for i, (s, d) in enumerate(zip(sources, dests_single)):
    #    pick_up(p1000)
    #    source = binding_buffer[i//96]  # 1 tube of binding buffer can accommodate all samples here
    #    h = h_track(275, source)
        # custom mix
    #    for _ in range(10):
    #        p1000.aspirate(500, source.bottom(h))
    #        p1000.dispense(500, source.bottom(h+20))
    #    p1000.transfer(275, source.bottom(h), d.bottom(5), air_gap=100,
    #                   mix_after=(10, 100), new_tip='never')
    #    p1000.air_gap(100)
    #    p1000.drop_tip()

    # transfer internal control + proteinase K
    #for d in dests_multi:
    #    pick_up(m20)
    #    m20.transfer(10, ic_pk.bottom(2), d.bottom(10), air_gap=5,
    #                 new_tip='never')
    #    m20.air_gap(5)
    #    m20.drop_tip()

    ctx.comment('Terminado.')

    # track final used tip
    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips300': tip_log['count'][p300],
        #    'tips20': tip_log['count'][m20]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)
