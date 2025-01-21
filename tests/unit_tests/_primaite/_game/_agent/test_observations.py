# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import List

import pytest
import yaml

from primaite.game.agent.observations import ObservationManager
from primaite.game.agent.observations.file_system_observations import FileObservation, FolderObservation
from primaite.game.agent.observations.host_observations import HostObservation


class TestFileSystemRequiresScan:
    @pytest.mark.parametrize(
        ("yaml_option_string", "expected_val"),
        (
            ("file_system_requires_scan: true", True),
            ("file_system_requires_scan: false", False),
            (" ", True),
        ),
    )
    def test_obs_config(self, yaml_option_string, expected_val):
        """Check that the default behaviour is to set FileSystemRequiresScan to True."""
        obs_cfg_yaml = f"""
      type: CUSTOM
      options:
        components:
          - type: NODES
            label: NODES
            options:
              hosts:
                - hostname: domain_controller
                - hostname: web_server
                  services:
                    - service_name: WebServer
                - hostname: database_server
                  folders:
                    - folder_name: database
                      files:
                      - file_name: database.db
                - hostname: backup_server
                - hostname: security_suite
                - hostname: client_1
                - hostname: client_2
              num_services: 1
              num_applications: 0
              num_folders: 1
              num_files: 1
              num_nics: 2
              include_num_access: false
              {yaml_option_string}
              include_nmne: true
              monitored_traffic:
                icmp:
                    - NONE
                tcp:
                    - DNS
              routers:
                - hostname: router_1
              num_ports: 0
              ip_list:
                - 192.168.1.10
                - 192.168.1.12
                - 192.168.1.14
                - 192.168.1.16
                - 192.168.1.110
                - 192.168.10.21
                - 192.168.10.22
                - 192.168.10.110
              wildcard_list:
                - 0.0.0.1
              port_list:
                - 80
                - 5432
              protocol_list:
                - ICMP
                - TCP
                - UDP
              num_rules: 10

          - type: LINKS
            label: LINKS
            options:
              link_references:
                - router_1:eth-1<->switch_1:eth-8
                - router_1:eth-2<->switch_2:eth-8
                - switch_1:eth-1<->domain_controller:eth-1
                - switch_1:eth-2<->web_server:eth-1
                - switch_1:eth-3<->database_server:eth-1
                - switch_1:eth-4<->backup_server:eth-1
                - switch_1:eth-7<->security_suite:eth-1
                - switch_2:eth-1<->client_1:eth-1
                - switch_2:eth-2<->client_2:eth-1
                - switch_2:eth-7<->security_suite:eth-2
          - type: "NONE"
            label: ICS
            options: {{}}

        """

        cfg = yaml.safe_load(obs_cfg_yaml)
        manager = ObservationManager(config=cfg)

        hosts: List[HostObservation] = manager.obs.components["NODES"].hosts
        for i, host in enumerate(hosts):
            folders: List[FolderObservation] = host.folders
            for j, folder in enumerate(folders):
                assert folder.file_system_requires_scan == expected_val  # Make sure folders require scan by default
                files: List[FileObservation] = folder.files
                for k, file in enumerate(files):
                    assert file.file_system_requires_scan == expected_val

    def test_file_require_scan(self):
        file_state = {"health_status": 3, "visible_status": 1}

        obs_requiring_scan = FileObservation([], include_num_access=False, file_system_requires_scan=True)
        assert obs_requiring_scan.observe(file_state)["health_status"] == 1

        obs_not_requiring_scan = FileObservation([], include_num_access=False, file_system_requires_scan=False)
        assert obs_not_requiring_scan.observe(file_state)["health_status"] == 3

    def test_folder_require_scan(self):
        folder_state = {"health_status": 3, "visible_status": 1}

        obs_requiring_scan = FolderObservation(
            [], files=[], num_files=0, include_num_access=False, file_system_requires_scan=True
        )
        assert obs_requiring_scan.observe(folder_state)["health_status"] == 1

        obs_not_requiring_scan = FolderObservation(
            [], files=[], num_files=0, include_num_access=False, file_system_requires_scan=False
        )
        assert obs_not_requiring_scan.observe(folder_state)["health_status"] == 3
