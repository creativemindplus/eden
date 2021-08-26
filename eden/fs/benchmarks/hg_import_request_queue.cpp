/*
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This software may be used and distributed according to the terms of the
 * GNU General Public License version 2.
 */

#include "eden/fs/benchharness/Bench.h"
#include "eden/fs/config/ReloadableConfig.h"
#include "eden/fs/store/ImportPriority.h"
#include "eden/fs/store/hg/HgImportRequest.h"
#include "eden/fs/store/hg/HgImportRequestQueue.h"
#include "eden/fs/utils/IDGen.h"

namespace {

using namespace facebook::eden;

Hash uniqueHash() {
  std::array<uint8_t, Hash::RAW_SIZE> bytes = {0};
  auto uid = generateUniqueID();
  std::memcpy(bytes.data(), &uid, sizeof(uid));
  return Hash{bytes};
}

HgImportRequest makeBlobImportRequest(
    ImportPriority priority,
    RequestMetricsScope::LockedRequestWatchList& pendingImportWatches) {
  auto hgRevHash = uniqueHash();
  auto proxyHash = HgProxyHash{RelativePath{"some_blob"}, hgRevHash};
  auto hash = proxyHash.sha1();
  auto importTracker =
      std::make_unique<RequestMetricsScope>(&pendingImportWatches);
  return HgImportRequest::makeBlobImportRequest(
             hash, std::move(proxyHash), priority, std::move(importTracker))
      .first;
}

void enqueue(benchmark::State& state) {
  auto rawEdenConfig = EdenConfig::createTestEdenConfig();
  auto edenConfig = std::make_shared<ReloadableConfig>(
      rawEdenConfig, ConfigReloadBehavior::NoReload);

  RequestMetricsScope::LockedRequestWatchList pendingImportWatches;
  auto queue = HgImportRequestQueue{edenConfig};

  std::vector<HgImportRequest> requests;
  requests.reserve(state.max_iterations);
  for (size_t i = 0; i < state.max_iterations; i++) {
    requests.emplace_back(
        makeBlobImportRequest(ImportPriority::kNormal(), pendingImportWatches));
  }

  auto requestIter = requests.begin();
  for (auto _ : state) {
    auto& request = *requestIter++;
    auto inProgress = queue.checkImportInProgress<Blob>(
        request.getRequest<HgImportRequest::BlobImport>()->proxyHash,
        ImportPriority::kNormal());
    XDCHECK(!inProgress.has_value());
    queue.enqueue(std::move(request));
  }
}

BENCHMARK(enqueue)
    ->Unit(benchmark::kNanosecond)
    ->Threads(1)
    ->Threads(2)
    ->Threads(4)
    ->Threads(8)
    ->Threads(16)
    ->Threads(32);
} // namespace

EDEN_BENCHMARK_MAIN();