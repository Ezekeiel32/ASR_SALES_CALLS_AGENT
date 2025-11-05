#!/usr/bin/env python3
"""
RunPod Utilities - Python utilities for managing RunPod Serverless deployments

Usage:
    python runpod_utils.py --help
    python runpod_utils.py test-endpoint --endpoint-id ep-xxxxx --api-key your_key
    python runpod_utils.py get-status --endpoint-id ep-xxxxx --job-id job_xxxxx --api-key your_key
    python runpod_utils.py submit-job --endpoint-id ep-xxxxx --api-key your_key --meeting-id uuid --organization-id uuid --audio-s3-key s3://bucket/key
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional

import requests


class RunPodClient:
    """Client for interacting with RunPod Serverless API"""

    BASE_URL = "https://api.runpod.io/v2"
    TIMEOUT = 30

    def __init__(self, endpoint_id: str, api_key: str):
        """
        Initialize RunPod client

        Args:
            endpoint_id: RunPod endpoint ID (e.g., ep-xxxxx)
            api_key: RunPod API key
        """
        self.endpoint_id = endpoint_id
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def submit_job(self, input_data: Dict[str, Any]) -> str:
        """
        Submit a job to the RunPod endpoint

        Args:
            input_data: Input data for the job

        Returns:
            Job ID

        Raises:
            RuntimeError: If submission fails
        """
        url = f"{self.BASE_URL}/{self.endpoint_id}/run"
        payload = {"input": input_data}

        try:
            response = requests.post(
                url, json=payload, headers=self.headers, timeout=self.TIMEOUT
            )
            response.raise_for_status()
            result = response.json()

            if "id" not in result:
                raise RuntimeError(f"No job ID in response: {result}")

            return result["id"]
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to submit job: {e}")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a submitted job

        Args:
            job_id: RunPod job ID

        Returns:
            Job status information

        Raises:
            RuntimeError: If request fails
        """
        url = f"{self.BASE_URL}/{self.endpoint_id}/status/{job_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get job status: {e}")

    def wait_for_job(
        self, job_id: str, timeout: int = 300, poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for a job to complete

        Args:
            job_id: RunPod job ID
            timeout: Maximum wait time in seconds
            poll_interval: Interval between status checks in seconds

        Returns:
            Final job status

        Raises:
            TimeoutError: If job doesn't complete within timeout
            RuntimeError: If job fails
        """
        start_time = time.time()
        elapsed = 0

        while elapsed < timeout:
            status = self.get_job_status(job_id)

            print(f"Job {job_id}: {status.get('status', 'UNKNOWN')} (elapsed: {elapsed}s)")

            if status.get("status") == "COMPLETED":
                print("✓ Job completed successfully")
                return status
            elif status.get("status") == "FAILED":
                error_msg = status.get("error", "Unknown error")
                raise RuntimeError(f"Job failed: {error_msg}")

            time.sleep(poll_interval)
            elapsed = int(time.time() - start_time)

        raise TimeoutError(f"Job did not complete within {timeout} seconds")


def test_endpoint(args: argparse.Namespace) -> None:
    """Test RunPod endpoint connectivity"""
    print("Testing RunPod endpoint connectivity...")
    print(f"Endpoint ID: {args.endpoint_id}")

    try:
        client = RunPodClient(args.endpoint_id, args.api_key)

        # Submit a simple test job
        test_payload = {
            "test": True,
            "message": "Health check from runpod_utils.py",
        }

        print("Submitting test job...")
        job_id = client.submit_job(test_payload)
        print(f"✓ Test job submitted successfully (Job ID: {job_id})")

        # Wait for result
        print("Waiting for result...")
        result = client.wait_for_job(job_id, timeout=60)

        print("\n✓ Test successful!")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"✗ Test failed: {e}", file=sys.stderr)
        sys.exit(1)


def get_status(args: argparse.Namespace) -> None:
    """Get status of a submitted job"""
    try:
        client = RunPodClient(args.endpoint_id, args.api_key)
        status = client.get_job_status(args.job_id)

        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"✗ Failed to get status: {e}", file=sys.stderr)
        sys.exit(1)


def submit_job(args: argparse.Namespace) -> None:
    """Submit a meeting processing job"""
    try:
        client = RunPodClient(args.endpoint_id, args.api_key)

        # Build job input
        input_data = {
            "meeting_id": args.meeting_id,
            "organization_id": args.organization_id,
        }

        if args.audio_s3_key:
            input_data["audio_s3_key"] = args.audio_s3_key

        print(f"Submitting meeting processing job...")
        print(f"Meeting ID: {args.meeting_id}")
        print(f"Organization ID: {args.organization_id}")
        if args.audio_s3_key:
            print(f"Audio S3 Key: {args.audio_s3_key}")

        job_id = client.submit_job(input_data)
        print(f"✓ Job submitted successfully (Job ID: {job_id})")

        # Optionally wait for completion
        if args.wait:
            print("\nWaiting for job completion...")
            result = client.wait_for_job(job_id, timeout=args.timeout)
            print("\n✓ Job completed!")
            print(json.dumps(result, indent=2))
        else:
            print(f"\nTo check status, run:")
            print(
                f"  python runpod_utils.py get-status --endpoint-id {args.endpoint_id} "
                f"--job-id {job_id} --api-key <your_key>"
            )

    except Exception as e:
        print(f"✗ Failed to submit job: {e}", file=sys.stderr)
        sys.exit(1)


def batch_submit(args: argparse.Namespace) -> None:
    """Submit multiple meetings for batch processing"""
    try:
        # Read meeting data from file
        if not os.path.exists(args.file):
            print(f"✗ File not found: {args.file}", file=sys.stderr)
            sys.exit(1)

        with open(args.file, "r") as f:
            meetings = json.load(f)

        if not isinstance(meetings, list):
            print("✗ File must contain a JSON array of meetings", file=sys.stderr)
            sys.exit(1)

        client = RunPodClient(args.endpoint_id, args.api_key)
        results = []

        print(f"Submitting {len(meetings)} meetings for batch processing...")

        for i, meeting in enumerate(meetings, 1):
            print(f"[{i}/{len(meetings)}] Submitting {meeting.get('meeting_id')}...")

            try:
                job_id = client.submit_job(meeting)
                results.append(
                    {
                        "meeting_id": meeting.get("meeting_id"),
                        "job_id": job_id,
                        "status": "submitted",
                    }
                )
                print(f"  ✓ Job ID: {job_id}")

                # Optional delay between submissions
                if args.delay:
                    time.sleep(args.delay)

            except Exception as e:
                results.append(
                    {
                        "meeting_id": meeting.get("meeting_id"),
                        "status": "failed",
                        "error": str(e),
                    }
                )
                print(f"  ✗ Failed: {e}")

        # Write results
        output_file = args.output or "batch_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Batch submission complete!")
        print(f"Results saved to: {output_file}")

        successful = sum(1 for r in results if r["status"] == "submitted")
        failed = sum(1 for r in results if r["status"] == "failed")
        print(f"Submitted: {successful}, Failed: {failed}")

    except Exception as e:
        print(f"✗ Batch submission failed: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="RunPod Serverless utilities for managing deployments"
    )

    # Global arguments
    parser.add_argument(
        "--endpoint-id",
        help="RunPod endpoint ID",
        default=os.getenv("RUNPOD_ENDPOINT_ID"),
    )
    parser.add_argument(
        "--api-key", help="RunPod API key", default=os.getenv("RUNPOD_API_KEY")
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # test-endpoint command
    test_parser = subparsers.add_parser(
        "test-endpoint", help="Test RunPod endpoint connectivity"
    )
    test_parser.set_defaults(func=test_endpoint)

    # get-status command
    status_parser = subparsers.add_parser("get-status", help="Get job status")
    status_parser.add_argument("--job-id", required=True, help="RunPod job ID")
    status_parser.set_defaults(func=get_status)

    # submit-job command
    submit_parser = subparsers.add_parser(
        "submit-job", help="Submit a meeting processing job"
    )
    submit_parser.add_argument("--meeting-id", required=True, help="Meeting UUID")
    submit_parser.add_argument("--organization-id", required=True, help="Organization UUID")
    submit_parser.add_argument("--audio-s3-key", help="S3 key for audio file")
    submit_parser.add_argument(
        "--wait", action="store_true", help="Wait for job completion"
    )
    submit_parser.add_argument(
        "--timeout", type=int, default=300, help="Timeout in seconds (default: 300)"
    )
    submit_parser.set_defaults(func=submit_job)

    # batch-submit command
    batch_parser = subparsers.add_parser(
        "batch-submit", help="Submit multiple meetings for batch processing"
    )
    batch_parser.add_argument(
        "--file", required=True, help="JSON file with meeting data"
    )
    batch_parser.add_argument(
        "--output", help="Output file for results (default: batch_results.json)"
    )
    batch_parser.add_argument(
        "--delay", type=float, help="Delay between submissions in seconds"
    )
    batch_parser.set_defaults(func=batch_submit)

    args = parser.parse_args()

    # Validate required arguments
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if not args.endpoint_id:
        print(
            "✗ --endpoint-id required (or set RUNPOD_ENDPOINT_ID env var)",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.api_key:
        print("✗ --api-key required (or set RUNPOD_API_KEY env var)", file=sys.stderr)
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
