"""Regression checks for failures that previously produced misleading PASS/gaps."""
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch
from ping_metrics import metrics
import nm_tests as lab


def trace(sequences, tx=20, stop=2.1):
    lines = ['START 0.0']
    for seq in range(1, tx+1):
        suffix = f'64 bytes from x: icmp_seq={seq} ttl=60 time=1 ms' if seq in sequences else f'no answer yet for icmp_seq={seq}'
        lines.append(f'[{seq/10:.2f}] {suffix}')
    lines += [f'{tx} packets transmitted, {len(sequences)} received', f'STOP {stop}']
    return '\n'.join(lines)


class RunnerChecks(unittest.TestCase):
    def test_initial_loss_is_in_gap(self):
        data = metrics(trace(set(range(11, 21))))
        self.assertEqual(data['lost'], 10)
        self.assertEqual(data['max_gap_s'], 1.1)
        self.assertTrue(data['recovered'])

    def test_total_loss_has_nonzero_gap(self):
        data = metrics(trace(set()))
        self.assertEqual(data['max_gap_s'], 2.1)
        self.assertFalse(data['recovered'])

    def test_tail_is_unrecovered(self):
        data = metrics(trace(set(range(1, 11))))
        self.assertEqual(data['max_gap_s'], 1.1)
        self.assertFalse(data['recovered'])

    def test_empty_measurement_is_invalid(self):
        with self.assertRaises(ValueError):
            metrics('20 packets transmitted, 0 received')

    def test_changed_ike_fails(self):
        good = metrics(trace(set(range(1, 21))))
        self.assertEqual(lab.verdict('seg2', 'any', 'seg2', False, [good, good]), 'FAIL')

    def test_total_loss_cannot_pass_any(self):
        bad = metrics(trace(set()))
        self.assertEqual(lab.verdict('seg2', 'any', 'seg2', True, [bad, bad]), 'FAIL')

    def test_negative_control_requires_both_blocked(self):
        good, bad = metrics(trace(set(range(1, 21)))), metrics(trace(set()))
        self.assertEqual(lab.verdict('seg1', 'blocked', 'seg1', True, [good, bad]), 'FAIL')
        self.assertEqual(lab.verdict('seg1', 'blocked', 'seg1', True, [bad, bad]), 'PASS')

    def test_multiple_owners_are_visible(self):
        self.assertEqual(lab.owner({'seg1': {'act': 'active'}, 'seg2': {'act': 'eligible'}}), 'MULTIPLE:seg1,seg2')

    def test_failed_precondition_never_starts_traffic(self):
        with patch.object(lab, 'wait', side_effect=lab.LabError('timeout')), \
             patch.object(lab, 'LOG', None), patch.object(lab, 'log'), patch.object(lab, 'start_traffic') as start:
            with self.assertRaises(lab.LabError):
                lab.begin('check', 'check')
            start.assert_not_called()

    def test_recovery_requires_new_replies_after_action(self):
        with patch.object(lab, 'docker', return_value=trace(set(range(1, 21)))), \
             patch.object(lab.time, 'time', return_value=2.1), patch.object(lab, 'AFTER', 1.2):
            self.assertFalse(lab.traffic_stable())

    def test_empty_measurement_cannot_pass(self):
        self.assertEqual(lab.verdict('seg1', 'any', 'seg1', True, []), 'INVALID')

    def test_rejoin_requires_a_unique_owner(self):
        good = metrics(trace(set(range(1, 21))))
        self.assertEqual(lab.verdict('unique', 'any', 'seg3', True, [good, good]), 'PASS')
        self.assertEqual(lab.verdict('unique', 'any', 'MULTIPLE:seg1,seg3', True, [good, good]), 'FAIL')

    def test_missing_private_forwarding_route_blocks_candidate(self):
        text = '100.64.1.0/24 Remote BGP\n100.64.2.0/24 Remote BGP\n'
        with patch.object(lab, 'op', return_value=text):
            self.assertFalse(lab.forwarding_ready('seg1'))

    def test_planned_switch_never_uses_unready_candidate(self):
        with patch.object(lab, 'wait', side_effect=[None, lab.LabError('no routes')]), \
             patch.object(lab, 'owner', return_value='seg2'), patch.object(lab, 'action') as action:
            with self.assertRaises(lab.LabError):
                lab.switch_to('seg1')
            action.assert_not_called()

    def test_bfd_off_removes_group_override(self):
        with patch.object(lab, 'cfg') as cfg:
            lab.bfd(False)
            self.assertEqual(cfg.call_count, 4)
            for call in cfg.call_args_list:
                for command in call.args[1:]:
                    self.assertTrue(command.startswith('delete /configure '))
                    self.assertNotIn(' false', command)

    def test_pin_replaces_import_chain_instead_of_appending(self):
        with patch.object(lab, 'cfg') as cfg:
            lab.pin_route('public', 'seg3')
        for call in cfg.call_args_list[1:]:
            self.assertTrue(call.args[1].startswith('delete '))
            self.assertTrue(call.args[1].endswith(' import'))
            self.assertIn(' import policy [', call.args[2])
        self.assertIn('["accept-all"]', cfg.call_args_list[-1].args[2])

    def test_ha_bootstrap_preserves_core_and_netns_and_cold_starts_cpm(self):
        events = []
        with tempfile.TemporaryDirectory() as tmp, patch.object(lab, 'RUN', Path(tmp)), \
             patch.object(lab, 'owner', return_value='seg1'), patch.object(lab, 'log'), \
             patch.object(lab, 'op', return_value='High Availability : (Not Specified)\n  2 isa2-tunnel up up'), \
             patch.object(lab, 'cfg', side_effect=lambda node, command: events.append(command)), \
             patch.object(lab.Path, 'read_text', return_value='MemAvailable: 12000000 kB\nSwapFree: 10000000 kB'), \
             patch.object(lab, 'run', side_effect=lambda args: events.append('memory ceiling')), \
             patch.object(lab, 'node_power', side_effect=lambda nodes, verb: events.append((nodes, verb))), \
             patch.object(lab.time, 'sleep'), patch.object(lab, 'wait'), patch.object(lab, 'readiness_probes'):
            lab.prepare_pool(True)
        self.assertEqual(events, [
            (('seg1', 'seg2'), 'stop'),
            '/configure card 1 mda 2 admin-state disable',
            '/configure isa tunnel-member-pool "pool1" high-availability tunnel-limit-32k',
            (('seg3',), 'stop'), 'memory ceiling', (('seg3',), 'start'),
            '/configure card 1 mda 2 admin-state enable',
            (('seg1',), 'start'), (('seg2',), 'start')])

    def test_pool_maintenance_rejects_active_or_ambiguous_owner(self):
        for owner in ('seg3', 'MULTIPLE:seg1,seg3', 'none'):
            with self.subTest(owner=owner), patch.object(lab, 'owner', return_value=owner), \
                 patch.object(lab, 'op', return_value='High Availability : (Not Specified)'), \
                 patch.object(lab, 'cfg') as cfg:
                with self.assertRaises(lab.LabError):
                    lab.prepare_pool(True)
                cfg.assert_not_called()

    def test_low_memory_blocks_ha_before_any_allocation(self):
        with patch.object(lab, 'owner', return_value='seg1'), \
             patch.object(lab, 'op', return_value='High Availability : (Not Specified)'), \
             patch.object(lab.Path, 'read_text', return_value='MemAvailable: 1000 kB\nSwapFree: 1000 kB'), \
             patch.object(lab, 'cfg') as cfg, patch.object(lab, 'run') as run, \
             patch.object(lab, 'node_power') as power, patch.object(lab, 'log'), \
             patch.object(lab, 'wait'), patch.object(lab.time, 'sleep'):
            with self.assertRaises(lab.LabError):
                lab.prepare_pool(True)
            cfg.assert_not_called()
            run.assert_not_called()
            self.assertEqual(power.call_args_list[-2].args, (('seg1',), 'start'))
            self.assertEqual(power.call_args_list[-1].args, (('seg2',), 'start'))

    def test_outstanding_notice_is_not_eventual_packet_loss(self):
        text = trace(set(range(1, 21)))
        text = text.replace('[1.90]', '[1.89] no answer yet for icmp_seq=19\n[1.90]')
        self.assertTrue(lab.initial_probe_valid(text))
        self.assertFalse(lab.initial_probe_valid(trace(set(range(2, 21)))))

    def test_cleanup_repairs_failed_pool_before_waiting_for_nominal(self):
        events = []
        with patch.object(lab, 'running', return_value=True), patch.object(lab, 'wait'), \
             patch.object(lab, 'unpin'), patch.object(lab, 'bfd'), patch.object(lab, 'cfg'), \
             patch.object(lab, 'owner', return_value='seg1'), patch.object(lab, 'op', return_value='revertive false'), \
             patch.object(lab, 'snapshot'), patch.object(lab, 'log'), patch.object(lab, 'action'), \
             patch.object(lab, 'prepare_pool', side_effect=lambda mode: events.append('pool repaired')), \
             patch.object(lab, 'baseline', side_effect=lambda: events.append('nominal required')):
            lab.cleanup()
        self.assertEqual(events, ['pool repaired', 'nominal required'])

    def test_cleanup_moves_owner_off_ds_before_pool_maintenance(self):
        events = []
        with patch.object(lab, 'running', return_value=True), patch.object(lab, 'wait'), \
             patch.object(lab, 'unpin'), patch.object(lab, 'bfd'), patch.object(lab, 'cfg'), \
             patch.object(lab, 'owner', return_value='seg3'), patch.object(lab, 'op'), \
             patch.object(lab, 'snapshot'), patch.object(lab, 'log'), patch.object(lab, 'action'), \
             patch.object(lab, 'prepare_pool', side_effect=lambda mode: events.append('pool')), \
             patch.object(lab, 'baseline', side_effect=lambda *target: events.append(('baseline', target))):
            lab.cleanup()
        self.assertEqual(events, [('baseline', ('seg1',)), 'pool', ('baseline', ())])

    def test_failed_ha_observation_still_restarts_both_das(self):
        with patch.object(lab, 'owner', return_value='seg1'), patch.object(lab, 'log'), \
             patch.object(lab, 'op', return_value='High Availability : (Not Specified)'), \
             patch.object(lab.Path, 'read_text', return_value='MemAvailable: 12000000 kB'), \
             patch.object(lab, 'cfg'), patch.object(lab, 'run'), patch.object(lab, 'wait'), \
             patch.object(lab.time, 'sleep'), patch.object(lab, 'node_power') as power:
            with self.assertRaisesRegex(lab.LabError, 'lost operational state'):
                lab.prepare_pool(True)
        self.assertEqual([call.args for call in power.call_args_list[-2:]],
                         [(('seg1',), 'start'), (('seg2',), 'start')])


if __name__ == '__main__':
    unittest.main()
