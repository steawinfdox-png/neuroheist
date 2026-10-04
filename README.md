# NeuroHeist

## Run the website and MRI API locally

Install the frontend and backend dependencies, then start the combined server:

```bash
cd neuroheist
npm install
cd ..
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
./scripts/start_local.sh
```

Open `http://127.0.0.1:8000`. The script builds the frontend with a same-origin API URL, then serves the frontend and FastAPI from port 8000. If `backend/brats_mri_segmentation.pth` is absent and `MODEL_URL` is unset, it downloads the [MONAI BraTS checkpoint](https://github.com/Project-MONAI/model-zoo/blob/dev/models/brats_mri_segmentation/large_files.yml) and verifies its SHA-256 digest. Place your own compatible checkpoint at that path to use it instead. The checkpoint stays out of Git.

The local script uses `INFERENCE_SHAPE=64,128,128`. The hosted backend defaults to `32,64,64` to fit its smaller memory budget. The original [MONAI model](https://github.com/Project-MONAI/model-zoo/blob/dev/models/brats_mri_segmentation/configs/metadata.json) was trained for four MRI modalities; single-volume 3D scans are accepted by copying their one channel to all four inputs, but those predictions have not been clinically validated.

For a local upload test, use [`samples/BRATS_457_3D.nii.gz`](samples/BRATS_457_3D.nii.gz). The four-channel source is [`samples/BRATS_457.nii.gz`](samples/BRATS_457.nii.gz).

## Publish through Cloudflare Tunnel

The domain remains registered at Porkbun. Its Cloudflare nameservers are `destiny.ns.cloudflare.com` and `quentin.ns.cloudflare.com`. This changes DNS hosting, not domain registration.

A locally managed tunnel named `neuroheist` is configured on this machine. Its ID is `83ceafdb-f2b4-4570-b2d3-ba8be6c5f59a`, and its private credentials and ingress config are in `/root/.cloudflared`. The Cloudflare apex record points to this tunnel. To restart it after reboot, run the local server above, then run:

```bash
cloudflared tunnel --config /root/.cloudflared/neuroheist.yml run neuroheist
```

The tunnel uses HTTP/2 because outbound UDP to Cloudflare is blocked on this network. Keep this machine and both processes running for the public site to remain available. Once Porkbun has the assigned Cloudflare nameservers, check `https://neuroheist.select/health` and upload the sample 3D scan through the website.

On this machine, both processes are installed as `neuroheist.service` and `neuroheist-tunnel.service` under systemd. Use `systemctl status neuroheist.service neuroheist-tunnel.service` to check them, or `journalctl -u neuroheist.service -u neuroheist-tunnel.service -f` to follow their logs.

The local network's DNS resolvers currently answer `NXDOMAIN` for this new domain, although public resolvers return Cloudflare. A temporary `/etc/hosts` entry on this machine points `neuroheist.select` to a Cloudflare edge IP so the local browser can use the site. Remove that entry when the network DNS resolves the domain normally; it is a local workaround, not a DNS record for visitors.
