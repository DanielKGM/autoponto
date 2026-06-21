from django.http import QueryDict
from django.test import TestCase

from api.models import NoBorda
from api.services.sincronizacao_borda import ENTIDADES_SYNC, montar_payload_pull


class EdgePullSnapshotTests(TestCase):
    def test_pull_returns_authoritative_snapshot_without_incremental_contract(self):
        no = NoBorda.objects.create(codigo="NO-CCET-01", nome="No CCET")
        query_params = QueryDict("node_id=NO-CCET-01&cursors=valor-legado")

        payload = montar_payload_pull(no, query_params)

        self.assertEqual(set(payload), {"data", "synced_at"})
        self.assertEqual(set(payload["data"]), set(ENTIDADES_SYNC))
        self.assertTrue(payload["synced_at"])
