"""
Comprehensive Test Runner - Executes all Backbone framework tests
"""
import asyncio
import sys
import os
import traceback

# Add backbone to path for testing
sys.path.insert(0, os.path.dirname(__file__))

# Import test modules
from tests.test_domain import run_domain_tests
from tests.test_infrastructure import run_infrastructure_tests
from tests.test_application import run_application_tests
from tests.test_interfaces import run_interface_tests


async def run_all_tests():
    """Run comprehensive test suite for Backbone framework"""
    
    print("🚀 Backbone Framework - Comprehensive Test Suite")
    print("=" * 60)
    print("Testing Clean Architecture implementation with event-driven microservices\n")
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    # Test categories to run
    test_categories = [
        ("Domain Layer", run_domain_tests),
        ("Infrastructure Layer", run_infrastructure_tests),
        ("Application Layer", run_application_tests),
        ("Interface Layer", run_interface_tests),
    ]
    
    start_time = asyncio.get_event_loop().time()
    
    for category_name, test_runner in test_categories:
        print(f"\n{'=' * 20} {category_name} {'=' * 20}")
        
        try:
            if asyncio.iscoroutinefunction(test_runner):
                await test_runner()
            else:
                test_runner()
                
        except Exception as e:
            error_msg = f"{category_name} tests failed: {str(e)}"
            test_results["errors"].append(error_msg)
            test_results["failed"] += 1
            
            print(f"\n❌ {category_name} FAILED:")
            print(f"   Error: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
        else:
            test_results["passed"] += 1
            print(f"✅ {category_name} completed successfully")
    
    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏆 TEST SUITE SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total execution time: {duration:.2f} seconds")
    print(f"✅ Test categories passed: {test_results['passed']}")
    print(f"❌ Test categories failed: {test_results['failed']}")
    print(f"📊 Success rate: {(test_results['passed'] / len(test_categories)) * 100:.1f}%")
    
    if test_results["errors"]:
        print("\n❌ Errors encountered:")
        for error in test_results["errors"]:
            print(f"   • {error}")
    
    print("\n🎯 Framework Components Tested:")
    print("   🏗️  Clean Architecture with strict layer separation")
    print("   🔢 8-digit exception system with error codes by layer")
    print("   🎯 Specification pattern for dynamic filtering")
    print("   📋 Repository pattern with mock implementations")
    print("   🔧 Response builders for consistent API responses")
    print("   📊 Structured logging with context management")
    print("   🧪 Complete testing framework with base test cases")
    print("   🔄 Event-driven architecture with:")
    print("      • Domain, integration, and system events")
    print("      • Event stores (in-memory and file-based)")
    print("      • Event validation and status tracking")
    print("      • Hexagonal architecture for event handling")
    
    if test_results["failed"] == 0:
        print("\n🎉 ALL TESTS PASSED! Framework is ready for production use.")
        return 0
    else:
        print(f"\n⚠️  {test_results['failed']} test categories failed. Please review errors above.")
        return 1


async def run_specific_layer_tests(layer: str):
    """Run tests for a specific layer"""
    
    layer_tests = {
        "domain": ("Domain Layer", run_domain_tests),
        "infrastructure": ("Infrastructure Layer", run_infrastructure_tests),
        "application": ("Application Layer", run_application_tests),
        "interface": ("Interface Layer", run_interface_tests),
    }
    
    if layer.lower() not in layer_tests:
        print(f"❌ Unknown layer: {layer}")
        print(f"Available layers: {', '.join(layer_tests.keys())}")
        return 1
    
    category_name, test_runner = layer_tests[layer.lower()]
    
    print(f"🧪 Running {category_name} Tests")
    print("=" * 40)
    
    try:
        if asyncio.iscoroutinefunction(test_runner):
            await test_runner()
        else:
            test_runner()
        
        print(f"\n✅ {category_name} tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ {category_name} tests failed:")
        print(f"   Error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return 1


def show_help():
    """Show help information"""
    print("Backbone Framework Test Runner")
    print("=" * 40)
    print("\nUsage:")
    print("  python test_runner.py                    # Run all tests")
    print("  python test_runner.py [layer]           # Run specific layer tests")
    print("  python test_runner.py --help            # Show this help")
    print("\nAvailable layers:")
    print("  domain           # Test domain layer (entities, specifications, exceptions)")
    print("  infrastructure   # Test infrastructure layer (logging, persistence, adapters)")
    print("  application      # Test application layer (use cases, services, events)")
    print("  interface        # Test interface layer (response builders, controllers)")
    print("\nExamples:")
    print("  python test_runner.py domain")
    print("  python test_runner.py infrastructure")


async def main():
    """Main entry point"""
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ["--help", "-h", "help"]:
            show_help()
            return 0
        elif arg in ["domain", "infrastructure", "application", "interface"]:
            return await run_specific_layer_tests(arg)
        else:
            print(f"❌ Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
            return 1
    
    # Run all tests by default
    return await run_all_tests()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)