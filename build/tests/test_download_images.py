from build.download_images import local_gallery_paths

def test_local_gallery_paths():
    assert local_gallery_paths("brooches-llama", 2) == [
        "images/brooches-llama/0.jpg", "images/brooches-llama/1.jpg"]

def test_local_gallery_paths_zero():
    assert local_gallery_paths("x-y", 0) == []
