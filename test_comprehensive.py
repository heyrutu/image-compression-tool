"""
Comprehensive test to find bugs in the image compression workflow
"""
import os
import tempfile
import shutil
from io import BytesIO
from PIL import Image
from werkzeug.datastructures import FileStorage
from app import app, db, User, ImageRecord, compress_image

# Create a temporary directory for testing
test_dir = tempfile.mkdtemp()
print(f"Test directory: {test_dir}")

with app.app_context():
    db.create_all()
    
    print("\n" + "=" * 70)
    print("BUG TEST: Checking compress_image with different image formats")
    print("=" * 70)
    
    test_cases = [
        ('JPEG', 'image.jpg', 'RGB'),
        ('PNG', 'image.png', 'RGBA'),
        ('WEBP', 'image.webp', 'RGB'),
        ('BMP', 'image.bmp', 'RGB'),
    ]
    
    for fmt_name, filename, mode in test_cases:
        print(f"\nTesting {fmt_name}:")
        
        # Create a test image
        test_img = Image.new(mode, (800, 600), color=(255, 100, 50))
        
        # Save to BytesIO
        img_bytes = BytesIO()
        save_kwargs = {}
        if fmt_name == 'JPEG':
            if mode in ('RGBA', 'P'):
                test_img = test_img.convert('RGB')
            img_bytes_temp = BytesIO()
            test_img.save(img_bytes_temp, format='JPEG', quality=75)
            img_bytes = img_bytes_temp
        else:
            test_img.save(img_bytes, format=fmt_name)
        
        img_bytes.seek(0)
        
        # Create FileStorage object
        file_storage = FileStorage(
            stream=img_bytes,
            filename=filename,
            content_type='image/jpeg' if fmt_name == 'JPEG' else f'image/{fmt_name.lower()}'
        )
        
        try:
            stored_filename, original_size, compressed_size, fmt = compress_image(file_storage, 75, False)
            percent_saved = round((1 - (compressed_size / original_size)) * 100, 1) if original_size > 0 else 0
            
            print(f"  ✓ Successfully compressed")
            print(f"    Original: {original_size:,} bytes")
            print(f"    Compressed: {compressed_size:,} bytes")
            print(f"    Saved: {percent_saved}%")
            print(f"    Format: {fmt}")
            
            # Clean up
            stored_path = os.path.join(app.config['UPLOAD_FOLDER'] if 'UPLOAD_FOLDER' in app.config else 'static/uploads', stored_filename)
            if os.path.exists(stored_path):
                os.remove(stored_path)
        except Exception as e:
            print(f"  ✗ FAILED: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("BUG TEST: Testing with shrink_large option")
    print("=" * 70)
    
    # Create a large image
    test_img = Image.new('RGB', (4000, 3000), color=(200, 100, 50))
    img_bytes = BytesIO()
    test_img.save(img_bytes, format='JPEG', quality=75)
    img_bytes.seek(0)
    
    file_storage = FileStorage(
        stream=img_bytes,
        filename='large_image.jpg',
        content_type='image/jpeg'
    )
    
    try:
        stored_filename, original_size, compressed_size, fmt = compress_image(file_storage, 75, True)
        percent_saved = round((1 - (compressed_size / original_size)) * 100, 1) if original_size > 0 else 0
        
        print(f"\n✓ Successfully compressed with shrink_large=True")
        print(f"  Original: {original_size:,} bytes")
        print(f"  Compressed: {compressed_size:,} bytes")
        print(f"  Saved: {percent_saved}%")
        
        # Clean up
        stored_path = os.path.join(app.config['UPLOAD_FOLDER'] if 'UPLOAD_FOLDER' in app.config else 'static/uploads', stored_filename)
        if os.path.exists(stored_path):
            os.remove(stored_path)
    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

# Clean up
shutil.rmtree(test_dir, ignore_errors=True)
