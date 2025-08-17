#!/usr/bin/env python3
"""
Course Verification Integration - Clean version for testing with real data
"""

import os
import json
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from service.course_verification.course_verifier import CourseVerifier
from dotenv import load_dotenv

load_dotenv()


async def verify_session_transcript(transcript_file_path: str):
    """
    Verify course information in a session transcript file.
    """
    try:
        # Load transcript data
        with open(transcript_file_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        print(f"📄 Loading transcript: {transcript_file_path}")
        print(f"🆔 Session ID: {transcript_data.get('session_id', 'N/A')}")

        
        # Initialize course verifier
        verifier = CourseVerifier()
        
        # Verify the transcript
        print("🔍 Starting course verification...")
        verification_result = verifier.verify_full_transcript(transcript_data)
        
        # Display results
        print("\n" + "="*60)
        print("📊 COURSE VERIFICATION RESULTS")
        print("="*60)
        
        print(f"📈 Overall Accuracy Score: {verification_result['accuracy_score']:.2f}")
        print(f"📚 Courses Mentioned: {len(verification_result['courses_mentioned'])}")
        
        if verification_result['red_flags']:
            print(f"🚩 Red Flags: {len(verification_result['red_flags'])}")
            for flag in verification_result['red_flags']:
                print(f"   • {flag}")
        
        print(f"\n📝 Summary: {verification_result['overall_summary']}")
        
        # Detailed course analysis
        if verification_result['courses_mentioned']:
            print(f"\n🎓 DETAILED COURSE ANALYSIS")
            print("-" * 40)
            
            for i, course in enumerate(verification_result['courses_mentioned'], 1):
                print(f"\n{i}. {course['name']}")
                print(f"   Status: {course['match_status']} ({course['confidence_score']:.2f} confidence)")
                
                if course.get('claimed_duration'):
                    print(f"   Duration: {course['claimed_duration']} → {course.get('catalog_duration', 'Not found')}")
                
                if course.get('claimed_fee'):
                    print(f"   Fee: {course['claimed_fee']} → {course.get('catalog_fee', 'Not found')}")
                
                print(f"   Notes: {course['notes']}")
        
        # Save results
        output_dir = Path("verification_results")
        output_dir.mkdir(exist_ok=True)
        
        session_id = transcript_data.get('session_id', 'unknown')
        output_file = output_dir / f"verification_{session_id}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(verification_result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        return verification_result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """CLI interface for course verification."""
    
    if len(sys.argv) < 2:
        print("Usage: python course_verification_integration.py <transcript_file.json>")
        print("\nExample:")
        print("python course_verification_integration.py assets/transcripts_raw/chunk_123.json")
        sys.exit(1)
    
    transcript_file = sys.argv[1]
    
    if not os.path.exists(transcript_file):
        print(f"❌ Error: Transcript file not found: {transcript_file}")
        sys.exit(1)
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Error: Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        sys.exit(1)
    
    print("🚀 Starting Course Verification")
    print("=" * 50)
    
    # Run verification
    import asyncio
    result = asyncio.run(verify_session_transcript(transcript_file))
    
    if result:
        print("\n✅ Verification completed successfully!")
        
        # Quick summary
        accuracy = result['accuracy_score']
        if accuracy >= 0.9:
            print("🟢 High accuracy - counselor information appears reliable")
        elif accuracy >= 0.7:
            print("🟡 Moderate accuracy - some discrepancies found")
        else:
            print("🔴 Low accuracy - significant issues detected")
    
    else:
        print("\n❌ Verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
