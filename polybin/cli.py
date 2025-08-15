import argparse, os, sys, random
from .api import build

def main():
    parser = argparse.ArgumentParser(
        prog="polybin",
        description="📂 polybin: <tba>",
        add_help=False,
        usage="polybin <output> [--ico path.ico] [--mp4 path.mp4] [--zip path.zip ...]"
    )

    parser.add_argument("output", type=str, help="Output file name")
    parser.add_argument("--ico", type=str, help="Path to icon file (ICO format)")
    parser.add_argument("--mp4", type=str, help="Path to MP4 file")
    parser.add_argument("--zip", type=str, dest="zips", action="append", help="Path to a ZIP-like archive (repeatable)")
    parser.add_argument("-h", "--help", action="help", help="Show help and exit.")

    args = parser.parse_args()

    wants_ico = bool(args.ico)
    wants_mp4 = bool(args.mp4)
    wants_zip = bool(args.zips)

    if wants_zip and len(args.zips) > 1:
        pass
    else:
        if sum([wants_ico, wants_mp4, wants_zip]) < 2:
            print("❌ You must specify at least two of --ico/--mp4/--zip.")
            sys.exit(1)
    try:
        build(
            output_path=args.output,
            ico_path=args.ico,
            mp4_path=args.mp4,
            zip_paths=args.zips or []
        )
    except Exception as e:
        print(f"❌ Build failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
