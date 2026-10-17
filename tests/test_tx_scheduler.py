"""Drive the actual package action graph with asynchronous completion and fake time.

This is a deliberately narrow ESPHome scheduler seam: compile all production
conditions, callback lambdas, validators and JSON builders unchanged in C++.
Only script/wait/delay dispatch and the radio are doubles. Unknown YAML actions
fail the harness build, rather than being ignored. No copy of the RF validators
or production state transitions is used in this test.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/fixtures/rf_contract.json").read_text())


class Loader(yaml.SafeLoader):
    pass


class Lambda(str):
    pass


Loader.add_constructor("!lambda", lambda loader, node: Lambda(loader.construct_scalar(node)))


def load_package():
    return yaml.load((ROOT / "firmware/packages/rf-airbridge.yaml").read_text(), Loader=Loader)


def cpp_value(value):
    if isinstance(value, Lambda):
        return "([&]() { " + value + " })()"
    if isinstance(value, bool):
        return str(value).lower()
    return json.dumps(value)


def expression(condition):
    if "lambda" in condition:
        return "([&]() -> bool { " + condition["lambda"] + " })()"
    if "not" in condition:
        return "!(" + expression(condition["not"]) + ")"
    if condition == {"script.is_running": "rf_send_job"}:
        return "worker_running"
    raise AssertionError(f"Unsupported condition in scheduler seam: {condition}")


def millis(value):
    if value.endswith("ms"):
        return int(value[:-2])
    if value.endswith("s"):
        return int(value[:-1]) * 1000
    raise AssertionError(f"Unsupported delay: {value}")


def compile_actions(actions, params, substitutions):
    result = []
    for node in actions:
        if len(node) != 1:
            raise AssertionError(f"Unsupported action shape {node}")
        kind, action = next(iter(node.items()))
        if kind == "lambda":
            result.append("{\n" + action + "\n}")
        elif kind == "if":
            result.append("if (" + expression(action["condition"]) + ") {\n" +
                          compile_actions(action["then"], params, substitutions) + "\n} else {\n" +
                          compile_actions(action.get("else", []), params, substitutions) + "\n}")
        elif kind == "script.execute":
            assert action["id"] == "rf_send_job"
            assert set(action) == set(params) | {"id"}
            result.append("start_worker(" + ",".join(cpp_value(action[p]) for p in params) + ");")
        elif kind.startswith("remote_transmitter.transmit_"):
            assert action["transmitter_id"] == "rf_transmitter"
            assert action["repeat"]["wait_time"] == "10ms"
            fields = (["id", "channel", "button", "check"] if kind.endswith("dooya") else ["code", "protocol"])
            values = [cpp_value(action[key]) for key in fields] + [cpp_value(action["repeat"]["times"])]
            encoder = "capture_dooya" if kind.endswith("dooya") else "capture_rc"
            result.append(encoder + "(" + ",".join(values) + "); begin_transmit();")
        elif kind == "mqtt.publish_json":
            topic, payload = action["topic"], action["payload"]
            for key, value in substitutions.items():
                topic = topic.replace("${" + key + "}", str(value))
                payload = payload.replace("${" + key + "}", str(value))
            assert "${" not in topic + payload
            result.append("{ Json root;\n" + payload + "\npublish(" + json.dumps(topic) + "," +
                          cpp_value(action["qos"]) + "," + cpp_value(action["retain"]) + ",root); }")
        else:
            raise AssertionError(f"Unsupported action in scheduler seam: {kind}")
    return "\n".join(result)


def generate_harness(package):
    worker, = package["script"]
    assert worker["id"] == "rf_send_job" and worker["mode"] == "single"
    params = worker["parameters"]
    types = {"bool": "bool", "int": "int", "string": "std::string"}
    declaration = ",".join(types[t] + " " + name for name, t in params.items())
    code = lambda nodes: compile_actions(nodes, params, package["substitutions"])
    steps = worker["then"]
    waits = [i for i, step in enumerate(steps) if "wait_until" in step]
    assert len(waits) == 1, "Async TX requires one explicit completion wait"
    index = waits[0]
    assert list(steps[-1]) == ["delay"], "Worker must remain busy through trailing cooldown"
    delay = millis(steps[-1]["delay"])
    assert delay == 750
    wait = steps[index]["wait_until"]
    header = '\n#include "tx_scheduler_stubs.h"\n'
    header += "struct Request {" + "".join(types[t] + " " + n + ";" for n, t in params.items()) + "};\n"
    header += "Request current;\nvoid start_worker(" + declaration + ");\nvoid pump();\n"
    header += "void on_complete() {\n" + code(package["remote_transmitter"]["on_complete"]["then"]) + "\n}\n"
    header += "void begin_transmit() { assert(!tx_pending); ++tx_count; tx_pending=true; tx_due=now_ms+next_tx_delay;\n"
    header += code(package["remote_transmitter"]["on_transmit"]["then"]) + "\n}\n"
    for action in package["api"]["actions"]:
        arguments = ",".join(types[t] + " " + n for n, t in action["variables"].items())
        header += "void " + action["action"] + "(" + arguments + ") {\n" + code(action["then"]) + "\n}\n"
    header += "bool wait_ready() { return " + expression(wait["condition"]) + "; }\n"
    header += "void finish_worker() { waiting=false;\n"
    header += "\n".join("auto &" + p + " = current." + p + ";" for p in params) + "\n"
    header += code(steps[index + 1:-1]) + f"\ncooldown=true; ready_at=now_ms+{delay};\n}}\n"
    header += "void start_worker(" + declaration + ") { assert(!worker_running); worker_running=true;\n"
    header += "current={" + ",".join(params) + "};\n" + code(steps[:index]) + "\n"
    header += f"waiting=true; wait_deadline=now_ms+{millis(wait['timeout'])}; pump();\n}}\n"
    header += r'''
void pump() {
  if (tx_pending && now_ms >= tx_due) { tx_pending=false; on_complete(); }
  if (waiting && (wait_ready() || now_ms >= wait_deadline)) finish_worker();
  if (cooldown && now_ms >= ready_at) { cooldown=false; worker_running=false; }
}
void advance(uint64_t target) {
  while (now_ms < target) {
    uint64_t next = target;
    if (tx_pending && tx_due > now_ms) next = std::min(next,tx_due);
    if (waiting && wait_deadline > now_ms) next = std::min(next,wait_deadline);
    if (cooldown && ready_at > now_ms) next = std::min(next,ready_at);
    now_ms=next; pump();
  }
}
void request(bool dooya) {
  if (dooya) send_dooya_code(1193046,1,1,2,3);
  else send_rf_code("00000001",1,3);
}
int main(int argc,char **argv) {
  assert(argc==2);
  const std::string scenario=argv[1];
  if (scenario.rfind("cross",0)==0) {
    const bool first=scenario[5]=='1', second=scenario[6]=='1';
    request(first);
    assert(worker_running && rf_tx_active && !rf_receiver.enabled);
    assert(messages.empty() && tx_count==1);
    advance(999); request(second);
    assert(messages.size()==1 && tx_count==1);
    advance(1000);
    assert(messages.size()==2 && worker_running && !rf_tx_active && rf_receiver.enabled);
    advance(1749); request(second);
    assert(messages.size()==3 && tx_count==1);
    advance(1750); request(second);
    assert(tx_count==2);
    advance(2750); advance(4000);
    assert(!worker_running && messages.size()==4 && tx_count==2);
    const std::vector<std::string> one={"receiver.suspend","radio.idle","pin.low","radio.tx",
      "radio.idle","pin.release","radio.rx","receiver.resume"};
    auto expected=one; expected.insert(expected.end(),one.begin(),one.end());
    assert(trace==expected);
    assert(encoded_requests[0]==(first ? "dooya:1193046:1:1:2:3" : "rc:00000001:1:3"));
    assert(encoded_requests[1]==(second ? "dooya:1193046:1:1:2:3" : "rc:00000001:1:3"));
  } else if (scenario=="invalid") {
    request(false);
    send_rf_code("101",1,3);
    send_dooya_code(16777216,1,1,2,3);
    assert(tx_count==1 && messages.size()==2);
    advance(1750);
    assert(!worker_running && tx_count==1);
  } else if (scenario=="timeout") {
    next_tx_delay=40000;
    request(false); advance(29999);
    assert(messages.empty() && rf_tx_active);
    advance(30000);
    assert(messages.size()==1 && rf_tx_error && rf_tx_fault && rf_tx_active && !rf_receiver.enabled);
    // A timed-out transaction may still own RMT. A digital_write here could
    // race or block on that transaction; only put CC1101 into idle mode.
    assert((trace==std::vector<std::string>{"receiver.suspend","radio.idle","pin.low","radio.tx","radio.idle"}));
    advance(30750); request(true);
    assert(messages.size()==2 && tx_count==1);
    advance(40000);
    assert(!rf_receiver.enabled && rf_tx_active && tx_count==1);
  } else if (scenario=="resume_error") {
    rf_receiver.fail_resume=true;
    request(true); advance(1000);
    assert(messages.size()==1 && rf_tx_error && rf_tx_fault && rf_tx_active && !rf_receiver.enabled);
    advance(1750); request(false);
    assert(tx_count==1 && messages.size()==2);
  } else { assert(false); }
}
'''
    return header


class TxSchedulerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = load_package()
        directory = tempfile.TemporaryDirectory(prefix="rf-scheduler-")
        cls.addClassCleanup(directory.cleanup)
        root = Path(directory.name)
        source = root / "scheduler.cpp"
        source.write_text(generate_harness(cls.package))
        cls.binary = root / "scheduler"
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            raise RuntimeError("C++17 compiler required")
        flags = ["-std=c++17", "-Wall", "-Wextra"]
        if os.environ.get("RF_CPP_SANITIZERS") == "1":
            flags += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all", "-g", "-O1"]
        build = subprocess.run([compiler, *flags, "-I", str(ROOT / "tests/native"), "-I",
                                str(ROOT / "firmware/include"), str(source), "-o", str(cls.binary)],
                               capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stdout + build.stderr)

    def run_scenario(self, scenario):
        run = subprocess.run([str(self.binary), scenario], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        output = []
        for line in run.stdout.splitlines():
            kind, now, topic, payload = line.split(" ", 3)
            self.assertEqual((kind, topic), ("MQTT", FIXTURE["topics"]["result"]))
            output.append((int(now), json.loads(payload)))
        return output

    def test_cross_protocol_busy_until_actual_completion_and_cooldown_no_queue(self):
        for first in (0, 1):
            for second in (0, 1):
                with self.subTest(first=first, second=second):
                    messages = self.run_scenario(f"cross{first}{second}")
                    formats = ("rc_switch", "dooya")
                    busy = {"source": "rf", "format": formats[second], "status": "busy", "delivery_confirmed": False}
                    self.assertEqual(messages, [
                        (999, busy), (1000, FIXTURE["tx_examples"][formats[first]]),
                        (1749, busy), (2750, FIXTURE["tx_examples"][formats[second]])])

    def test_invalid_requests_remain_invalid_while_worker_is_busy(self):
        messages = self.run_scenario("invalid")
        self.assertEqual([message[1]["status"] for message in messages],
                         ["invalid_request", "invalid_request", "send_finished"])
        self.assertEqual([message[1]["format"] for message in messages], ["rc_switch", "dooya", "rc_switch"])
        for _, message in messages:
            self.assertIs(message["delivery_confirmed"], False)

    def test_timeout_latches_fault_and_late_completion_cannot_restore_receive(self):
        messages = self.run_scenario("timeout")
        self.assertEqual([m[0] for m in messages], [30000, 30750])
        for _, message in messages:
            self.assertEqual(message["status"], "send_failed")
            self.assertIs(message["receiver_resumed"], False)
            self.assertIs(message["delivery_confirmed"], False)

    def test_failed_receive_rearm_never_claims_success(self):
        for _, message in self.run_scenario("resume_error"):
            self.assertEqual(message["status"], "send_failed")
            self.assertIs(message["receiver_resumed"], False)

    def test_api_names_electrical_modes_and_native_event_contract(self):
        actions = {action["action"]: action["variables"] for action in self.package["api"]["actions"]}
        self.assertEqual(actions, FIXTURE["api"])
        tx = self.package["remote_transmitter"]
        self.assertTrue(tx["non_blocking"])
        self.assertFalse(tx["eot_level"])
        self.assertTrue(tx["pin"]["mode"]["open_drain"])
        self.assertTrue(tx["pin"]["mode"]["pullup"])
        self.assertEqual(tx["pin"]["number"], "GPIO4")
        rx = self.package["remote_receiver"]
        self.assertEqual(rx["pin"], "GPIO5")
        self.assertTrue(rx["filter"].endswith("us"))
        self.assertLessEqual(int(rx["filter"][:-2]), 170)
        event, = self.package["event"]
        self.assertEqual(event["event_types"], [f"button_{i}" for i in range(1, 9)])
        self.assertFalse(event["discovery"])
        self.assertFalse(event["retain"])
        self.assertEqual(self.package["mqtt"]["reboot_timeout"], "0s")


if __name__ == "__main__":
    unittest.main()
