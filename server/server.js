const express = require("express");
const multer = require("multer");
const compression = require("compression");
const zmq = require("zeromq");
const path = require("path");
const fs = require("fs");
const bodyParser = require('body-parser')

const storage = multer.diskStorage({
    destination: (_req, _file, cb) => {
        cb(null, "/app/server/uploads/");
    },
    filename: (_req, _file, cb) => {
        const uniqueSuffix = Date.now().toString();
        cb(null, uniqueSuffix);
    },
});

const upload = multer({ storage: storage });

const PORT = process.env.PORT || 3000;
const app = express();
const sock = new zmq.Request();

function init() {
    app.use(compression());
    app.use(bodyParser.urlencoded({ extended: false }))
    app.listen(PORT, () => {
        console.log("Exress listen on PORT: " + PORT);
    });
    app.get("/", (_req, res) => {
        res.send("hello");
    });
    sock.connect(
        process.env.WORKER_ADDRESS || "tcp://localhost:5555"
    );
}

async function main() {
    init();
    app.use("/static", express.static("static"));
    app.post(
        "/upload_image",
        upload.single("image"),
        async (req, res) => {
            const resultPath = await handleInferenceImage(
                path.join(req.file.path),
                req.body.threshold
            );

            const readStream = fs.createReadStream(resultPath);

            readStream.on("open", () => {
                res.setHeader(
                    "Content-Disposition",
                    "attachment; filename=image.png"
                );
                res.setHeader("Content-Type", "image/png");
                readStream.pipe(res);
            });

            readStream.on("error", (err) => {
                res.status(500).json({
                    message: err,
                });
            });

            readStream.on("close", () => {
                fs.unlink(resultPath, (err) => {
                    if (err) console.error(err);
                });
                fs.unlink(req.file.path, (err) => {
                    if (err) console.error(err);
                });
            });
        }
    );

    app.post(
        "/upload_video",
        upload.single("video"),
        async (req, res) => {
            res.json({
                name: req.file.filename + ".mp4"
            });
            sendInferenceVideoRequest(
                path.join(process.cwd(), req.file.path),
                req.file.filename,
                req.body.artifactId
            );
        }
    );
}

async function sendInferenceVideoRequest(
    path,
    filename,
    artifactId,
    threshold = 0.3
) {
    await sock.send(["video", threshold, path, filename, artifactId]);
    const [msg] = await sock.receive();
    // const filepath = msg.toString();
}

async function handleInferenceImage(path, threshold = 0.3) {
    await sock.send(["image", threshold, path, null, null]);
    const [msg] = await sock.receive();
    const resultPath = msg.toString();
    return resultPath;
}

main();
